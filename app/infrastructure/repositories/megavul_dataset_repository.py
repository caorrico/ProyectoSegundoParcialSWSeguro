from pathlib import Path

from app.domain.contracts import Dataset, DatasetRepository

class MegaVulDatasetRepository(DatasetRepository):
    def __init__(self, dataset_path: Path, limit: int = 500):
        self._dataset_path = dataset_path
        self._limit = limit

    def load(self) -> Dataset:
        import ijson
        dataset = []
        
        with open(self._dataset_path, "rb") as f:
            # We use ijson to parse large JSON files incrementally
            items = ijson.items(f, "item")
            count = 0
            for item in items:
                if count >= self._limit:
                    break
                
                # Vulnerable version (func_before)
                func_before = item.get("func_before")
                if func_before:
                    metrics_vuln = self._extract_metrics(func_before, is_vulnerable=1)
                    dataset.append(metrics_vuln)
                
                # Patched version (func)
                func_after = item.get("func")
                if func_after:
                    metrics_safe = self._extract_metrics(func_after, is_vulnerable=0)
                    dataset.append(metrics_safe)

                count += 1
                
        return dataset

    def save(self, dataset: Dataset) -> None:
        raise NotImplementedError("MegaVulDatasetRepository is read-only")

    def _extract_metrics(self, code: str, is_vulnerable: int) -> dict:
        return {
            "raw_code": code,
            "is_vulnerable": is_vulnerable
        }
