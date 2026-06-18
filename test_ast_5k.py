import sys, time
from pathlib import Path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import pandas as pd
from app.infrastructure.ml.ast_extractor import ASTFeatureExtractor
from app.infrastructure.ml.code_feature_extractor import SecurityPatternFeatureExtractor

FEATURE_COLUMNS = ["raw_code", "language", "source", "code_length", "line_count"]
csv_path = ROOT / "data" / "processed" / "combined_clean_vulnerability_dataset.csv"
df = pd.read_csv(csv_path, usecols=FEATURE_COLUMNS, nrows=5000)
corpus = df["raw_code"].tolist()
print(f"Loaded {len(corpus)} items"); sys.stdout.flush()

print("AST..."); sys.stdout.flush()
t0 = time.time()
ast = ASTFeatureExtractor()
r1 = ast.transform(corpus)
print(f"  {r1.shape} in {time.time()-t0:.1f}s"); sys.stdout.flush()

print("Security..."); sys.stdout.flush()
t0 = time.time()
sec = SecurityPatternFeatureExtractor()
r2 = sec.transform(corpus)
print(f"  {r2.shape} in {time.time()-t0:.1f}s"); sys.stdout.flush()

print(f"Total: {time.time()-t0:.1f}s"); sys.stdout.flush()
