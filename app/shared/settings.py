from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    base_dir: Path = Path(__file__).resolve().parents[2]
    dataset_path: Path = base_dir / "data" / "raw" / "vulnerability_dataset.csv"
    model_path: Path = base_dir / "models" / "vulnerability_model.joblib"
    metrics_report_path: Path = base_dir / "reports" / "metrics.json"
    random_state: int = 42
    test_size: float = 0.25


settings = Settings()
