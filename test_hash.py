"""
Try with larger HashingVectorizer (2^14) and more training data.
Train with XGBoost on sparse data (no dense conversion).
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
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from xgboost import XGBClassifier

RANDOM_STATE = 42
FEATURE_COLUMNS = ["raw_code", "language", "source", "code_length", "line_count"]

csv_path = ROOT / "data" / "processed" / "combined_clean_vulnerability_dataset.csv"
full = pd.read_csv(csv_path, usecols=FEATURE_COLUMNS + ["is_vulnerable", "group_id", "code_hash"])
print(f"Total: {len(full)}, Vuln: {full['is_vulnerable'].sum()} ({full['is_vulnerable'].mean()*100:.1f}%)")

# Larger oversampled dataset
MAX_RECORDS = 15000
vuln = full[full["is_vulnerable"] == 1].sample(n=min(7500, MAX_RECORDS//2), random_state=RANDOM_STATE)
safe = full[full["is_vulnerable"] == 0].sample(n=MAX_RECORDS - len(vuln), random_state=RANDOM_STATE)
df = pd.concat([vuln, safe], ignore_index=True).sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
print(f"Sample: {len(df)} vuln={df['is_vulnerable'].sum()} ({df['is_vulnerable'].mean()*100:.1f}%)")

real_df = df[~df["source"].isin({"owasp2025"})].copy()
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
print(f"Fit={len(fit_df)}(vuln={y_fit.sum()}) Train={len(train_df)}(vuln={y_train.sum()}) Test={len(test_df)}(vuln={y_test.sum()})")

# Try different HashingVectorizer sizes
for n_feat in [2**14, 2**13, 2**12]:
    print(f"\n{'='*60}")
    print(f" HashingVectorizer n_features={n_feat}")
    print(f"{'='*60}")
    
    feature_blocks = [
        ("ast", ASTFeatureExtractor(), "raw_code"),
        ("security", SecurityPatternFeatureExtractor(), "raw_code"),
        ("word_hash", HashingVectorizer(n_features=n_feat, ngram_range=(1, 2), alternate_sign=False, norm="l2"), "raw_code"),
        ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=True), ["language", "source"]),
        ("numeric", StandardScaler(with_mean=False), ["code_length", "line_count"]),
    ]
    feat_pipe = ColumnTransformer(feature_blocks)
    
    t0 = time.time()
    X_fit_feat = feat_pipe.fit_transform(X_fit)
    X_valid_feat = feat_pipe.transform(X_valid)
    X_train_feat = feat_pipe.fit_transform(X_train)
    X_test_feat = feat_pipe.transform(X_test)
    feat_time = time.time() - t0
    print(f"  Features: {X_train_feat.shape}, time={feat_time:.1f}s")
    
    ns = int((y_fit == 0).sum()); nv = int((y_fit == 1).sum())
    spw = max(ns / max(nv, 1), 1.0)
    
    # XGBoost with 500 trees, deeper
    clf = XGBClassifier(n_estimators=500, max_depth=10, learning_rate=0.1,
                        subsample=0.8, colsample_bytree=0.8,
                        scale_pos_weight=spw, n_jobs=1,
                        random_state=RANDOM_STATE)
    t0 = time.time()
    clf.fit(X_fit_feat, y_fit)
    valid_probs = clf.predict_proba(X_valid_feat)[:, 1]
    best_t, best_a = 0.5, accuracy_score(y_valid, (valid_probs >= 0.5).astype(int))
    for t in np.arange(0.05, 0.96, 0.01):
        p = (valid_probs >= t).astype(int)
        a = accuracy_score(y_valid, p)
        if a > best_a:
            best_a, best_t = a, t
    fit_time = time.time() - t0
    print(f"  Fit: time={fit_time:.1f}s, val_acc={best_a:.4f}@t={best_t:.2f}")
    
    # Evaluate on test at various thresholds
    test_probs = clf.predict_proba(X_test_feat)[:, 1]
    for t, label in [(best_t, f"t={best_t:.2f}"), (0.5, "t=0.50")]:
        preds = (test_probs >= t).astype(int)
        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        roc = roc_auc_score(y_test, test_probs)
        print(f"  {label}: acc={acc:.4f} prec={prec:.4f} rec={rec:.4f} f1={f1:.4f} roc={roc:.4f}")
