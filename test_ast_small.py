import sys, time
from pathlib import Path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

print("test1"); sys.stdout.flush()
from app.infrastructure.ml.ast_extractor import ASTFeatureExtractor
print("test2"); sys.stdout.flush()
from app.infrastructure.ml.code_feature_extractor import SecurityPatternFeatureExtractor
print("test3"); sys.stdout.flush()

import pandas as pd
FEATURE_COLUMNS = ["raw_code", "language", "source", "code_length", "line_count"]
csv_path = ROOT / "data" / "processed" / "combined_clean_vulnerability_dataset.csv"
print("test4"); sys.stdout.flush()

# Test with small sample first
df = pd.read_csv(csv_path, nrows=10, usecols=FEATURE_COLUMNS)
corpus = df["raw_code"].tolist()
print(f"Loaded {len(corpus)} items"); sys.stdout.flush()

print("Testing AST..."); sys.stdout.flush()
t0 = time.time()
ast = ASTFeatureExtractor()
result = ast.transform(corpus)
print(f"AST done: {result.shape} in {time.time()-t0:.1f}s"); sys.stdout.flush()

print("Testing security..."); sys.stdout.flush()
t0 = time.time()
sec = SecurityPatternFeatureExtractor()
result2 = sec.transform(corpus)
print(f"Security done: {result2.shape} in {time.time()-t0:.1f}s"); sys.stdout.flush()

print("All good"); sys.stdout.flush()
