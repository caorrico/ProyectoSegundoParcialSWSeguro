"""
Test: RandomForest vs XGBoost with various configs on balanced oversampled data.
Also test: XGBoost with early stopping and more estimators.
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
from sklearn.model_selection import GroupShuffleSplit, cross_val_score
from sklearn.metrics import accuracy_score
from sklearn.base import BaseEstimator, ClassifierMixin

RANDOM_STATE = 42
FEATURE_COLUMNS = ["raw_code", "language", "source", "code_length", "line_count"]

csv_path = ROOT / "data" / "processed" / "combined_clean_vulnerability_dataset.csv"
full = pd.read_csv(csv_path, usecols=FEATURE_COLUMNS + ["is_vulnerable", "group_id", "code_hash"])

# Oversample to 50/50
MAX_RECORDS = 8000
vuln = full[full["is_vulnerable"] == 1].sample(n=min(4000, MAX_RECORDS//2), random_state=RANDOM_STATE)
safe = full[full["is_vulnerable"] == 0].sample(n=MAX_RECORDS - len(vuln), random_state=RANDOM_STATE)
df = pd.concat([vuln, safe], ignore_index=True).sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)

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
print(f"Fit={len(fit_df)}(vuln={y_fit.sum()}) Valid={len(valid_df)}(vuln={y_valid.sum()}) "
      f"Train={len(train_df)}(vuln={y_train.sum()}) Test={len(test_df)}(vuln={y_test.sum()})")
print(f"  vuln%: fit={y_fit.mean()*100:.1f}% test={y_test.mean()*100:.1f}%")

# Features
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
print(f"  done ({time.time()-t0:.1f}s), shape={X_train_feat.shape}")

# Test 1: XGBoost default (100 trees, max_depth=6)
from xgboost import XGBClassifier
print("\n[1] XGBoost default (100, d6)")
ns = int((y_fit == 0).sum()); nv = int((y_fit == 1).sum())
spw = max(ns / max(nv, 1), 1.0)
clf = XGBClassifier(n_estimators=100, max_depth=6, scale_pos_weight=spw, n_jobs=1, random_state=RANDOM_STATE)
t0 = time.time()
clf.fit(X_fit_feat, y_fit)
valid_probs = clf.predict_proba(X_valid_feat)[:, 1]
best_t = 0.5
best_a = accuracy_score(y_valid, (valid_probs >= 0.5).astype(int))
for t in np.arange(0.05, 0.96, 0.01):
    p = (valid_probs >= t).astype(int)
    a = accuracy_score(y_valid, p)
    if a > best_a:
        best_a, best_t = a, t
test_acc = accuracy_score(y_test, (clf.predict_proba(X_test_feat)[:, 1] >= best_t).astype(int))
print(f"  fit_time={time.time()-t0:.1f}s, val_acc={best_a:.4f}@t={best_t:.2f}, test_acc={test_acc:.4f}")

# Test 2: XGBoost with max_depth=10, 500 trees
print("\n[2] XGBoost (500, d10)")
clf2 = XGBClassifier(n_estimators=500, max_depth=10, learning_rate=0.1,
                     subsample=0.8, colsample_bytree=0.8,
                     scale_pos_weight=spw, n_jobs=1, random_state=RANDOM_STATE)
t0 = time.time()
clf2.fit(X_fit_feat, y_fit)
valid_probs2 = clf2.predict_proba(X_valid_feat)[:, 1]
best_t2, best_a2 = 0.5, accuracy_score(y_valid, (valid_probs2 >= 0.5).astype(int))
for t in np.arange(0.05, 0.96, 0.01):
    p = (valid_probs2 >= t).astype(int)
    a = accuracy_score(y_valid, p)
    if a > best_a2:
        best_a2, best_t2 = a, t
test_acc2 = accuracy_score(y_test, (clf2.predict_proba(X_test_feat)[:, 1] >= best_t2).astype(int))
print(f"  fit_time={time.time()-t0:.1f}s, val_acc={best_a2:.4f}@t={best_t2:.2f}, test_acc={test_acc2:.4f}")

# Test 3: Random Forest
from sklearn.ensemble import RandomForestClassifier
print("\n[3] RandomForest (300 trees)")
# Convert to dense for RF (sparse may not work)
from scipy.sparse import issparse
if issparse(X_fit_feat):
    X_fit_d = X_fit_feat.toarray()
    X_valid_d = X_valid_feat.toarray()
    X_test_d = X_test_feat.toarray()
else:
    X_fit_d, X_valid_d, X_test_d = X_fit_feat, X_valid_feat, X_test_feat

rf = RandomForestClassifier(n_estimators=300, max_depth=20, n_jobs=-1,
                            class_weight="balanced", random_state=RANDOM_STATE)
t0 = time.time()
rf.fit(X_fit_d, y_fit)
valid_probs3 = rf.predict_proba(X_valid_d)[:, 1]
best_t3, best_a3 = 0.5, accuracy_score(y_valid, (valid_probs3 >= 0.5).astype(int))
for t in np.arange(0.05, 0.96, 0.01):
    p = (valid_probs3 >= t).astype(int)
    a = accuracy_score(y_valid, p)
    if a > best_a3:
        best_a3, best_t3 = a, t
test_acc3 = accuracy_score(y_test, (rf.predict_proba(X_test_d)[:, 1] >= best_t3).astype(int))
print(f"  fit_time={time.time()-t0:.1f}s, val_acc={best_a3:.4f}@t={best_t3:.2f}, test_acc={test_acc3:.4f}")

# Test 4: XGBoost with early stopping
print("\n[4] XGBoost early stopping (max 2000)")
import xgboost as xgb
dtrain = xgb.DMatrix(X_fit_feat, label=y_fit)
dvalid = xgb.DMatrix(X_valid_feat, label=y_valid)
dtest = xgb.DMatrix(X_test_feat, label=y_test)
params = {"max_depth":8,"learning_rate":0.1,"subsample":0.8,"colsample_bytree":0.8,
          "scale_pos_weight":spw,"seed":RANDOM_STATE,"n_jobs":1}
t0 = time.time()
model = xgb.train(params, dtrain, num_boost_round=2000,
                  evals=[(dtrain,"train"),(dvalid,"eval")],
                  early_stopping_rounds=50, verbose_eval=False)
test_probs4 = model.predict(dtest)
best_t4, best_a4 = 0.5, accuracy_score(y_valid, (model.predict(dvalid) >= 0.5).astype(int))
for t in np.arange(0.05, 0.96, 0.01):
    p = (model.predict(dvalid) >= t).astype(int)
    a = accuracy_score(y_valid, p)
    if a > best_a4:
        best_a4, best_t4 = a, t
test_acc4 = accuracy_score(y_test, (test_probs4 >= best_t4).astype(int))
print(f"  best_iter={model.best_iteration+1}, time={time.time()-t0:.1f}s, val_acc={best_a4:.4f}@t={best_t4:.2f}, test_acc={test_acc4:.4f}")

print(f"\nSummary:")
print(f"  1. XGBoost(100,d6):     test={accuracy_score(y_test, (clf.predict_proba(X_test_feat)[:,1] >= best_t).astype(int)):.4f}")
print(f"  2. XGBoost(500,d10):    test={test_acc2:.4f}")
print(f"  3. RandomForest(300):   test={test_acc3:.4f}")
print(f"  4. XGBoost(es,2000):    test={test_acc4:.4f}")
