import argparse
import json
from pathlib import Path
from typing import Any, Dict

from app.application.use_cases.predict_vulnerability import PredictVulnerabilityUseCase
from app.application.use_cases.train_vulnerability_model import TrainVulnerabilityModelUseCase
from app.infrastructure.ml.random_forest_predictor import RandomForestPredictor
from app.infrastructure.ml.random_forest_trainer import RandomForestTrainer
from app.infrastructure.repositories.csv_dataset_repository import CsvDatasetRepository
from app.interfaces.dtos import CodeModuleMetricsDTO
from app.shared.settings import settings


def build_train_use_case() -> TrainVulnerabilityModelUseCase:
    repository = CsvDatasetRepository(settings.dataset_path)
    trainer = RandomForestTrainer(
        model_path=settings.model_path,
        report_path=settings.metrics_report_path,
        random_state=settings.random_state,
        test_size=settings.test_size,
    )
    return TrainVulnerabilityModelUseCase(repository, trainer)


def build_predict_use_case() -> PredictVulnerabilityUseCase:
    predictor = RandomForestPredictor(settings.model_path)
    return PredictVulnerabilityUseCase(predictor)


def train_command(_: argparse.Namespace) -> None:
    metrics = build_train_use_case().execute()
    print(json.dumps({"status": "trained", "metrics": metrics}, indent=2))


def predict_command(args: argparse.Namespace) -> None:
    payload = _read_json(Path(args.input))
    metrics = CodeModuleMetricsDTO.from_dict(payload)
    prediction = build_predict_use_case().execute(metrics)
    print(json.dumps(prediction.to_dict(), indent=2))


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Input JSON must contain an object.")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Secure data mining vulnerability predictor")
    subparsers = parser.add_subparsers(required=True)

    train_parser = subparsers.add_parser("train", help="Train vulnerability prediction model")
    train_parser.set_defaults(func=train_command)

    predict_parser = subparsers.add_parser("predict", help="Predict vulnerability risk from JSON metrics")
    predict_parser.add_argument("--input", required=True, help="Path to JSON file with code metrics")
    predict_parser.set_defaults(func=predict_command)

    args = parser.parse_args()
    try:
        args.func(args)
    except (FileNotFoundError, TypeError, ValueError, json.JSONDecodeError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
