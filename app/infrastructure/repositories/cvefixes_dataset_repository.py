from pathlib import Path

import pandas as pd

from app.domain.contracts import Dataset


class CVEFixesDatasetRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> Dataset:
        if not self._path.exists():
            raise FileNotFoundError(
                f"Dataset not found at {self._path}."
            )
        df = pd.read_csv(self._path)
        # Drop any rows with missing values in 'code' or 'safety'
        df = df.dropna(subset=["code", "safety"])
        # Convert 'safety' column to 'is_vulnerable' (1 for vulnerable, 0 for safe)
        df["is_vulnerable"] = df["safety"].apply(lambda x: 1 if x == "vulnerable" else 0)
        # Rename 'code' to 'raw_code' for compatibility
        df["raw_code"] = df["code"]
        return df[["raw_code", "is_vulnerable", "language"]].to_dict(orient="records")
