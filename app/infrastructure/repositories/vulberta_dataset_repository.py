import json
from pathlib import Path
from typing import List, Dict

from app.domain.contracts import DatasetRepository


class VulBERTaDatasetRepository(DatasetRepository):
    """Repository for the VulBERTa (Imperial College London) vulnerability dataset."""

    def __init__(self, data_path: Path, limit: int | None = None) -> None:
        self._data_path = data_path
        self._limit = limit

    def load(self) -> List[Dict[str, object]]:
        if not self._data_path.exists():
            raise FileNotFoundError(
                f"VulBERTa dataset not found at {self._data_path}. "
                "Asegúrate de extraer el archivo data.zip de tal forma que exista la ruta especificada."
            )

        import pandas as pd
        df = pd.read_pickle(self._data_path)
        
        records: List[Dict[str, object]] = []
        vuln_count = 0
        safe_count = 0
        half = self._limit // 2 if self._limit is not None else None

        # In VulBERTa's pickle format, the code is typically in the 'func' column and target in 'label'
        for _, row in df.iterrows():
            code = str(row.get("func", ""))
            label = row.get("label", -1)

            if not code or label not in (0, 1):
                continue

            if self._limit is not None:
                if label == 1 and vuln_count < half:
                    records.append({"raw_code": code, "is_vulnerable": 1})
                    vuln_count += 1
                elif label == 0 and safe_count < half:
                    records.append({"raw_code": code, "is_vulnerable": 0})
                    safe_count += 1

                if vuln_count >= half and safe_count >= half:
                    break
            else:
                # No limit: take all data
                records.append({"raw_code": code, "is_vulnerable": label})
                if label ==1:
                    vuln_count +=1
                else:
                    safe_count +=1

        print(f"[VulBERTa MVD] Loaded {len(records)} samples (vuln={vuln_count}, safe={safe_count})")
        return records
