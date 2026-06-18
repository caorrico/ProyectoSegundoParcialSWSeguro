"""
Train on realistic imbalanced distribution (not oversampling).
"""
import sys, time
from pathlib import Path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")

from app.infrastructure.ml.ast_extractor import ASTFeatureExtractor
from app.infrastructure.ml.code_feature_extractor import SecurityPatternFeatureExtractor
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import cross_val_score, GroupShuffleSplit
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score, confusion_matrix
from xgboost import XGBClassifier
from sklearn.base import BaseEstimator, ClassifierMixin

RANDOM_STATE = 42
FEATURE_COLUMNS = ["raw_code", "language", "source", "code_length", "line_count"]
TARGET_ACC = 0.82

csv_path = ROOT / "data" / "processed" / "combined_clean_vulnerability_dataset.csv"
full = pd.read_csv(csv_path, usecols=FEATURE_COLUMNS + ["is_vulnerable", "group_id", "code_hash"])
print(f"Total: {len(full)}, Vuln: {full['is_vulnerable'].sum()} ({full['is_vulnerable'].mean()*100:.1f}%)")

# Take a larger sample WITHOUT oversampling to maintain real distribution
MAX_RECORDS = 15000
df = full.sample(n=MAX_RECORDS, random_state=RANDOM_STATE).reset_index(drop=True)
print(f"Sample: {len(df)} vuln={df['is_vulnerable'].sum()} ({df['is_vulnerable'].mean()*100:.1f}%)")

# Split
SYNTHETIC_SOURCES = {"owasp2025"}
real_df = df[~df["source"].isin(SYNTHETIC_SOURCES)].copy()
real_groups = real_df["group_id"].where(real_df["group_id"].astype(str).str.len() > 0, real_df["code_hash"])
gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=RANDOM_STATE)
train_real_idx, test_idx = next(gss.split(real_df, real_df["is_vulnerable"], groups=real_groups))
train_real_df = real_df.iloc[train_real_idx].copy()
test_df = real_df.iloc[test_idx].copy()
train_real_df = train_real_df[~train_real_df["code_hash"].isin(set(test_df["code_hash"]))].copy()
valid_groups = train_real_df["group_id"].where(train_real_df["group_id"].astype(str).str.len() > 0, train_real_df["code_hash"])
vss = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=RANDOM_STATE)
fit_idx, valid_idx = next(vss.split(train_real_df, train_real_df["is_vulnerable"], groups=valid_groups))
fit_df = train_real_df.iloc[fit_idx].copy()
valid_df = train_real_df.iloc[valid_idx].copy()
train_df = train_real_df.copy()

X_fit = fit_df[FEATURE_COLUMNS]; y_fit = fit_df["is_vulnerable"].astype(int)
X_valid = valid_df[FEATURE_COLUMNS]; y_valid = valid_df["is_vulnerable"].astype(int)
X_train = train_df[FEATURE_COLUMNS]; y_train = train_df["is_vulnerable"].astype(int)
X_test = test_df[FEATURE_COLUMNS]; y_test = test_df["is_vulnerable"].astype(int)
print(f"Fit={len(fit_df)}(vuln={y_fit.sum()}) Valid={len(valid_df)}(vuln={y_valid.sum()}) "
      f"Train={len(train_df)}(vuln={y_train.sum()}) Test={len(test_df)}(vuln={y_test.sum()})")
print(f"  vuln%: fit={y_fit.mean()*100:.1f}% valid={y_valid.mean()*100:.1f}% test={y_test.mean()*100:.1f}%")

# Feature extraction
feature_blocks = [
    ("ast", ASTFeatureExtractor(), "raw_code"),
    ("security", SecurityPatternFeatureExtractor(), "raw_code"),
    ("word_hash", HashingVectorizer(n_features=2**12, ngram_range=(1, 2), alternate_sign=False, norm="l2"), "raw_code"),
    ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=True), ["language", "source"]),
    ("numeric", StandardScaler(with_mean=False), ["code_length", "line_count"]),
]
feat_pipe = ColumnTransformer(feature_blocks)
print("Extracting features...")
t0 = time.time()
X_fit_feat = feat_pipe.fit_transform(X_fit)
X_valid_feat = feat_pipe.transform(X_valid)
X_train_feat = feat_pipe.fit_transform(X_train)
X_test_feat = feat_pipe.transform(X_test)
print(f"  done ({time.time()-t0:.1f}s), train shape={X_train_feat.shape}")

# Train with imbalanced data using scale_pos_weight
ns = int((y_fit == 0).sum()); nv = int((y_fit == 1).sum())
spw = max(ns / max(nv, 1), 1.0)
print(f"scale_pos_weight={spw:.2f} (safe:{ns}, vuln:{nv})")

clf = XGBClassifier(n_estimators=300, max_depth=8, learning_rate=0.1,
                    subsample=0.8, colsample_bytree=0.8,
                    scale_pos_weight=spw, n_jobs=1,
                    random_state=RANDOM_STATE)
print("Training...")
t0 = time.time()
clf.fit(X_fit_feat, y_fit)
valid_probs = clf.predict_proba(X_valid_feat)[:, 1]

best_t, best_a = 0.5, 0.0
for t in np.arange(0.05, 0.96, 0.01):
    p = (valid_probs >= t).astype(int)
    a = accuracy_score(y_valid, p)
    if a > best_a:
        best_a, best_t = a, t
print(f"  valid best: t={best_t:.2f} acc={best_a:.4f} ({time.time()-t0:.1f}s)")

# Full train
ns2 = int((y_train == 0).sum()); nv2 = int((y_train == 1).sum())
spw2 = max(ns2 / max(nv2, 1), 1.0)
clf2 = XGBClassifier(n_estimators=300, max_depth=8, learning_rate=0.1,
                     subsample=0.8, colsample_bytree=0.8,
                     scale_pos_weight=spw2, n_jobs=1,
                     random_state=RANDOM_STATE)
print("Full train...")
t0 = time.time()
clf2.fit(X_train_feat, y_train)
test_probs = clf2.predict_proba(X_test_feat)[:, 1]
print(f"  done ({time.time()-t0:.1f}s)")

for label, p in [("0.50", 0.5), (f"{best_t:.2f}", best_t)]:
    preds = (test_probs >= p).astype(int)
    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    roc = roc_auc_score(y_test, test_probs)
    cm = confusion_matrix(y_test, preds)
    print(f"t={label}: acc={acc:.4f} prec={prec:.4f} rec={rec:.4f} f1={f1:.4f} roc={roc:.4f} "
          f"tn={cm[0][0]} fp={cm[0][1]} fn={cm[1][0]} tp={cm[1][1]}")
    if abs(p - best_t) < 0.01:
        final_acc = acc

print(f"\nTarget={TARGET_ACC*100:.0f}% | Achieved={final_acc*100:.2f}% | "
      f"{'PASS' if final_acc >= TARGET_ACC else f'GAP: {(TARGET_ACC-final_acc)*100:.2f}%'}")

# Cross-validation
class XGBWrap(BaseEstimator, ClassifierMixin):
    def __init__(self):
        pass
    def fit(self, X, y):
        ns = int((y == 0).sum()); nv = int((y == 1).sum())
        sp = max(ns / max(nv, 1), 1.0)
        self.clf_ = XGBClassifier(n_estimators=300, max_depth=8, learning_rate=0.1,
                                   subsample=0.8, colsample_bytree=0.8,
                                   scale_pos_weight=sp, n_jobs=1, random_state=RANDOM_STATE)
        self.clf_.fit(X, y)
        return self
    def predict(self, X):
        return self.clf_.predict(X)

CV_SAMPLE = 1000
cv_df = fit_df.sample(n=CV_SAMPLE, random_state=RANDOM_STATE).reset_index(drop=True)
cv_X = feat_pipe.transform(cv_df[FEATURE_COLUMNS])
cv_y = cv_df["is_vulnerable"].astype(int)
print(f"\nCV (n={len(cv_df)}, vuln={cv_y.mean()*100:.1f}%)...")
t0 = time.time()
cv_scores = cross_val_score(XGBWrap(), cv_X, cv_y, cv=3, scoring="accuracy", n_jobs=1)
print(f"  CV: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f} [{time.time()-t0:.1f}s]")
print(f"  Per fold: {[round(s,4) for s in cv_scores]}")
