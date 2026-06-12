"""
ReVeal Dataset Repository.
Reads ReVeal dataset in JSONL format.
Fields: 'code' (source code), 'label' (0=safe, 1=vulnerable)
Source: Chromium and Debian vulnerability data.
"""
import json
from pathlib import Path
from app.domain.contracts import Dataset, DatasetRepository


class ReVealDatasetRepository(DatasetRepository):
    """Loads ReVeal vulnerability dataset."""

    def __init__(self, dataset_path: Path, limit: int = 3000):
        self._dataset_path = dataset_path
        self._limit = limit

    def load(self) -> Dataset:
        dataset = []

        if not self._dataset_path.exists():
            raise FileNotFoundError(
                f"ReVeal dataset not found at {self._dataset_path}. "
                "Please run scripts/download_reveal.py first."
            )

        with open(self._dataset_path, "r", encoding="utf-8") as f:
            count = 0
            for line in f:
                if count >= self._limit:
                    break

                try:
                    item = json.loads(line.strip())
                    code = item.get("code", "") or item.get("func", "") or item.get("functionSource", "")
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
        raise NotImplementedError("ReVealDatasetRepository is read-only")
