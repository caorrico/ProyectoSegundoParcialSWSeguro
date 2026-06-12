"""
D2A Dataset Repository.
Reads IBM D2A dataset in JSONL format.
Fields: 'functionSource' (code), 'label' (0=safe, 1=vulnerable)
"""
import json
from pathlib import Path
from app.domain.contracts import Dataset, DatasetRepository


class D2ADatasetRepository(DatasetRepository):
    """Loads IBM D2A vulnerability dataset (function task)."""

    def __init__(self, dataset_path: Path, limit: int = 3000):
        self._dataset_path = dataset_path
        self._limit = limit

    def load(self) -> Dataset:
        dataset = []

        if not self._dataset_path.exists():
            raise FileNotFoundError(
                f"D2A dataset not found at {self._dataset_path}. "
                "Please run scripts/download_d2a.py first."
            )

        with open(self._dataset_path, "r", encoding="utf-8") as f:
            count = 0
            for line in f:
                if count >= self._limit:
                    break

                try:
                    item = json.loads(line.strip())
                    # D2A 'function' task uses 'functionSource' for code
                    # and 'label' for vulnerability (0 or 1)
                    code = item.get("functionSource", "") or item.get("func", "") or item.get("code", "")
                    label = item.get("label", 0) or item.get("target", 0)

                    if code and len(code) > 20:
                        dataset.append({
                            "raw_code": code,
                            "is_vulnerable": int(label)
                        })
                        count += 1
                except json.JSONDecodeError:
                    continue

        return dataset

    def save(self, dataset: Dataset) -> None:
        raise NotImplementedError("D2ADatasetRepository is read-only")
