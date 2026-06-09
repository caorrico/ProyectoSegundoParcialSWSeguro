from pathlib import Path

import pandas as pd

from app.domain.contracts import Dataset


class CsvDatasetRepository:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> Dataset:
        if not self._path.exists():
            raise FileNotFoundError(
                f"Dataset not found at {self._path}. Run: python scripts/generate_dataset.py"
            )
        return pd.read_csv(self._path).to_dict(orient="records")

    def save(self, dataset: Dataset) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(dataset).to_csv(self._path, index=False)
