import sys, time
from pathlib import Path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")

print("0"); sys.stdout.flush()
RANDOM_STATE = 42
FEATURE_COLUMNS = ["raw_code", "language", "source", "code_length", "line_count"]

csv_path = ROOT / "data" / "processed" / "combined_clean_vulnerability_dataset.csv"
print("1"); sys.stdout.flush()
full = pd.read_csv(csv_path, usecols=FEATURE_COLUMNS + ["is_vulnerable", "group_id", "code_hash"])
print(f"2: {len(full)} rows"); sys.stdout.flush()

MAX_RECORDS = 8000
vuln = full[full["is_vulnerable"] == 1].sample(n=min(4000, MAX_RECORDS//2), random_state=RANDOM_STATE)
safe = full[full["is_vulnerable"] == 0].sample(n=MAX_RECORDS - len(vuln), random_state=RANDOM_STATE)
df = pd.concat([vuln, safe], ignore_index=True).sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
print(f"3: {len(df)} rows"); sys.stdout.flush()

from sklearn.model_selection import GroupShuffleSplit
SYNTHETIC_SOURCES = {"owasp2025"}
TEST_SIZE = 0.25
VALIDATION_SIZE = 0.20

real_df = df[~df["source"].isin(SYNTHETIC_SOURCES)].copy()
real_groups = real_df["group_id"].where(real_df["group_id"].astype(str).str.len() > 0, real_df["code_hash"])
print(f"4: {len(real_df)} real rows"); sys.stdout.flush()

gss = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
print(f"5"); sys.stdout.flush()
train_real_idx, test_idx = next(gss.split(real_df, real_df["is_vulnerable"], groups=real_groups))
print(f"6: train={len(train_real_idx)}, test={len(test_idx)}"); sys.stdout.flush()

train_real_df = real_df.iloc[train_real_idx].copy()
test_df = real_df.iloc[test_idx].copy()
train_real_df = train_real_df[~train_real_df["code_hash"].isin(set(test_df["code_hash"]))].copy()
print(f"7: train_real={len(train_real_df)}, test={len(test_df)}"); sys.stdout.flush()

valid_groups = train_real_df["group_id"].where(train_real_df["group_id"].astype(str).str.len() > 0, train_real_df["code_hash"])
vss = GroupShuffleSplit(n_splits=1, test_size=VALIDATION_SIZE, random_state=RANDOM_STATE)
fit_idx, valid_idx = next(vss.split(train_real_df, train_real_df["is_vulnerable"], groups=valid_groups))
fit_df = train_real_df.iloc[fit_idx].copy()
valid_df = train_real_df.iloc[valid_idx].copy()
train_df = train_real_df.copy()
print(f"8: fit={len(fit_df)}, valid={len(valid_df)}, train={len(train_df)}"); sys.stdout.flush()

X_fit = fit_df[FEATURE_COLUMNS]
print(f"9: X_fit shape={X_fit.shape}"); sys.stdout.flush()

from app.infrastructure.ml.ast_extractor import ASTFeatureExtractor
from app.infrastructure.ml.code_feature_extractor import SecurityPatternFeatureExtractor
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

print("10: Building feature blocks"); sys.stdout.flush()
feature_blocks = [
    ("ast", ASTFeatureExtractor(), "raw_code"),
    ("security", SecurityPatternFeatureExtractor(), "raw_code"),
    ("word_hash", HashingVectorizer(n_features=2**12, ngram_range=(1, 2), alternate_sign=False, norm="l2"), "raw_code"),
    ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=True), ["language", "source"]),
    ("numeric", StandardScaler(with_mean=False), ["code_length", "line_count"]),
]

print("11: Creating ColumnTransformer"); sys.stdout.flush()
feat_pipe = ColumnTransformer(feature_blocks)

print("12: Starting fit_transform"); sys.stdout.flush()
t0 = time.time()
X_fit_feat = feat_pipe.fit_transform(X_fit)
print(f"13: Done in {time.time()-t0:.1f}s, shape={X_fit_feat.shape}"); sys.stdout.flush()
