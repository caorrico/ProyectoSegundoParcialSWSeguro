import json
from pathlib import Path
from app.domain.contracts import Dataset, DatasetRepository

class CodeXGLUEDatasetRepository(DatasetRepository):
    def __init__(self, dataset_path: Path, limit: int | None = None):
        self._dataset_path = dataset_path
        self._limit = limit

    def load(self) -> Dataset:
        dataset = []
        
        if not self._dataset_path.exists():
            raise FileNotFoundError(f"CodeXGLUE dataset not found at {self._dataset_path}. Please run scripts/download_codexglue.py first.")
            
        with open(self._dataset_path, "r", encoding="utf-8") as f:
            count = 0
            for line in f:
                if self._limit is not None and count >= self._limit:
                    break
                
                try:
                    item = json.loads(line.strip())
                    code = item.get("func", "")
                    is_vulnerable = item.get("target", 0)
                    
                    if code:
                        dataset.append({
                            "raw_code": code,
                            "is_vulnerable": int(is_vulnerable)
                        })
                        count += 1
                except json.JSONDecodeError:
                    continue
                    
        return dataset

    def save(self, dataset: Dataset) -> None:
        raise NotImplementedError("CodeXGLUEDatasetRepository is read-only")
