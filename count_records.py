"""Count records in processed dataset."""
import pandas as pd
import sys
from pathlib import Path

root = Path(__file__).parent
csv_path = root / "data" / "processed" / "combined_clean_vulnerability_dataset.csv"

if not csv_path.exists():
    print("NO_COMBINED_CSV")
    sys.exit(0)

reader = pd.read_csv(csv_path, usecols=["is_vulnerable"], chunksize=100000)
total = 0
counts = {0: 0, 1: 0}
for chunk in reader:
    total += len(chunk)
    c = chunk["is_vulnerable"].value_counts().to_dict()
    counts[0] += c.get(0, 0)
    counts[1] += c.get(1, 0)

print(f"Total: {total}, Safe: {counts[0]}, Vulnerable: {counts[1]}, Vuln%: {counts[1]/total*100:.1f}%")
