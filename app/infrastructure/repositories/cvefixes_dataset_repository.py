import json
from pathlib import Path
import pandas as pd
from app.domain.contracts import Dataset

class CVEFixesDatasetRepository:
    def __init__(self, path: Path, limit: int = None) -> None:
        self._path = path
        self._limit = limit

    def load(self) -> Dataset:
        if not self._path.exists():
            raise FileNotFoundError(
                f"CVEFixes dataset not found at {self._path}. Please ensure it is downloaded."
            )
        
        raw_records = []
        if self._path.suffix == ".jsonl":
            with open(self._path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if self._limit and len(raw_records) >= self._limit:
                        break
                    if line.strip():
                        raw_records.append(json.loads(line))
        elif self._path.suffix == ".csv":
            df = pd.read_csv(self._path)
            if self._limit:
                df = df.head(self._limit)
            raw_records = df.to_dict(orient="records")
        else:
            raise ValueError(f"Unsupported CVEFixes dataset format: {self._path.suffix}")

        # Transform to standard format: raw_code and is_vulnerable
        processed_records = []
        for record in raw_records:
            # Vulnerable version
            if "vulnerable_code" in record and record["vulnerable_code"]:
                processed_records.append({
                    "raw_code": record["vulnerable_code"],
                    "is_vulnerable": 1
                })
            # Fixed version (safe sample)
            if "fixed_code" in record and record["fixed_code"]:
                processed_records.append({
                    "raw_code": record["fixed_code"],
                    "is_vulnerable": 0
                })
                
        return processed_records

    def save(self, dataset: Dataset) -> None:
        raise NotImplementedError("CVEFixes dataset is read-only")
