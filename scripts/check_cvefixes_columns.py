#!/usr/bin/env python3
"""Check CVEFixes columns."""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

cvefixes_path = project_root / "data/CVEFixes.csv/CVEFixes.csv"

if cvefixes_path.exists():
    import pandas as pd
    df = pd.read_csv(cvefixes_path, nrows=5)
    print("CVEFixes columns:")
    for col in df.columns:
        print(f"  - {col}")
    print("\nPrimeras 3 filas completas:")
    print(df.head(3).T)
else:
    print(f"No se encontró {cvefixes_path}")
