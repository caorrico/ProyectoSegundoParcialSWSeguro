import argparse
import json
from pathlib import Path
from typing import Any, Dict

from app.application.use_cases.predict_vulnerability import PredictVulnerabilityUseCase
from app.application.use_cases.train_vulnerability_model import TrainVulnerabilityModelUseCase
from app.infrastructure.ml.random_forest_predictor import RandomForestPredictor
from app.infrastructure.ml.random_forest_trainer import RandomForestTrainer
from app.infrastructure.ml.vulberta_trainer import VulBERTaTrainer
from app.infrastructure.repositories.csv_dataset_repository import CsvDatasetRepository
from app.interfaces.dtos import CodeModuleMetricsDTO
from app.shared.settings import settings


from app.infrastructure.repositories.megavul_dataset_repository import MegaVulDatasetRepository
from app.infrastructure.repositories.codexglue_dataset_repository import CodeXGLUEDatasetRepository
from app.infrastructure.repositories.combined_dataset_repository import CombinedDatasetRepository
from app.infrastructure.repositories.d2a_dataset_repository import D2ADatasetRepository
from app.infrastructure.repositories.reveal_dataset_repository import ReVealDatasetRepository
from app.infrastructure.repositories.vulberta_dataset_repository import VulBERTaDatasetRepository

class OWASPDatasetRepository:
    def __init__(self, path: Path):
        self.path = path
        
    def load(self):
        import json
        records = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records

def build_train_use_case(
    use_megavul: bool, language: str, use_codexglue: bool, use_combined: bool, use_d2a: bool, use_reveal: bool, use_vulberta: bool, use_owasp: bool, use_deep_learning: bool = False
) -> TrainVulnerabilityModelUseCase:
    if use_owasp:
        repository = OWASPDatasetRepository(Path("data/owasp2025/train.jsonl"))
    elif use_combined:
        repository = CombinedDatasetRepository(limit_per_source=2000)
    elif use_vulberta:
        repository = VulBERTaDatasetRepository(settings.base_dir / "data" / "data" / "finetune" / "mvd" / "mvd_train.pkl")
    elif use_reveal:
        reveal_path = Path("data/reveal/train.jsonl")
        repository = ReVealDatasetRepository(reveal_path, limit=3000)
    elif use_d2a:
        d2a_path = Path("data/d2a/train.jsonl")
        repository = D2ADatasetRepository(d2a_path, limit=3000)
    elif use_codexglue:
        codexglue_path = Path("data/codexglue/train.jsonl")
        repository = CodeXGLUEDatasetRepository(codexglue_path, limit=5000)
    elif use_megavul:
        megavul_path = Path(f"megavul/{language}/megavul_simple.json")
        repository = MegaVulDatasetRepository(megavul_path, limit=2000)
    else:
        repository = CsvDatasetRepository(settings.dataset_path)

    if use_deep_learning:
        trainer = VulBERTaTrainer(model_path=settings.model_path, report_path=settings.metrics_report_path)
    else:
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


def train_command(args: argparse.Namespace) -> None:
    use_megavul = getattr(args, "use_megavul", False)
    use_codexglue = getattr(args, "use_codexglue", False)
    use_combined = getattr(args, "use_combined", False)
    use_d2a = getattr(args, "use_d2a", False)
    use_reveal = getattr(args, "use_reveal", False)
    use_vulberta = getattr(args, "use_vulberta", False)
    use_owasp = getattr(args, "use_owasp", False)
    use_deep_learning = getattr(args, "use_deep_learning", False)
    tune = getattr(args, "tune", False)
    language = getattr(args, "language", "c_cpp")
    metrics = build_train_use_case(use_megavul, language, use_codexglue, use_combined, use_d2a, use_reveal, use_vulberta, use_owasp, use_deep_learning).execute(tune=tune)
    print(json.dumps({"status": "trained", "metrics": metrics}, indent=2))


def predict_command(args: argparse.Namespace) -> None:
    if args.raw_code:
        path = Path(args.raw_code)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        code = path.read_text(encoding="utf-8")
        from app.domain.entities import RawCodeModule
        metrics = RawCodeModule(raw_code=code)
    elif args.input:
        payload = _read_json(Path(args.input))
        metrics = CodeModuleMetricsDTO.from_dict(payload)
    else:
        raise ValueError("Either --input or --raw-code must be provided.")
        
    report_path = Path(args.shap_report) if args.shap_report else None
    prediction = build_predict_use_case().execute(metrics, report_path)
    print(json.dumps(prediction.to_dict(), indent=2))


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Input JSON must contain an object.")
    return payload


def scan_command(args: argparse.Namespace) -> None:
    """Scan an entire project directory for vulnerabilities."""
    import os
    from app.domain.entities import RawCodeModule

    target_dir = Path(args.directory)
    if not target_dir.is_dir():
        raise ValueError(f"'{target_dir}' is not a valid directory.")

    extensions = {".c", ".cpp", ".h", ".hpp", ".cc", ".cxx", ".java", ".py", ".js", ".ts", ".go", ".rs"}
    exclude_dirs = {".git", "node_modules", ".venv", "__pycache__", "venv", "build", "dist", ".tox"}

    use_case = build_predict_use_case()
    results = []

    # Collect all source files
    source_files = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if Path(f).suffix.lower() in extensions:
                source_files.append(Path(root) / f)

    if not source_files:
        print(f"No source files found in '{target_dir}'.")
        return

    print(f"\n{'='*70}")
    print(f"  VULNERABILITY SCAN REPORT")
    print(f"  Target: {target_dir.resolve()}")
    print(f"  Files to scan: {len(source_files)}")
    print(f"{'='*70}\n")

    for i, file_path in enumerate(source_files, 1):
        try:
            code = file_path.read_text(encoding="utf-8", errors="replace")
            metrics = RawCodeModule(raw_code=code)
            prediction = use_case.execute(metrics)
            rel_path = file_path.relative_to(target_dir)

            risk_icon = "[!!!]" if prediction.risk_level.value == "HIGH" else ("[??]" if prediction.risk_level.value == "MEDIUM" else "[OK]")
            prob_pct = f"{prediction.risk_probability * 100:.1f}%"

            results.append({
                "file": str(rel_path),
                "is_vulnerable": prediction.is_vulnerable,
                "risk_probability": prediction.risk_probability,
                "risk_level": prediction.risk_level.value,
            })

            print(f"  [{i:3d}/{len(source_files)}] {risk_icon} {prediction.risk_level.value:6s} ({prob_pct:>6s}) | {rel_path}")

        except Exception as e:
            print(f"  [{i:3d}/{len(source_files)}] [ERR] ERROR | {file_path.relative_to(target_dir)} - {e}")

    # Summary
    total = len(results)
    high = sum(1 for r in results if r["risk_level"] == "HIGH")
    medium = sum(1 for r in results if r["risk_level"] == "MEDIUM")
    low = sum(1 for r in results if r["risk_level"] == "LOW")
    vulnerable = sum(1 for r in results if r["is_vulnerable"])

    print(f"\n{'='*70}")
    print(f"  SCAN SUMMARY")
    print(f"{'='*70}")
    print(f"  Total files scanned : {total}")
    print(f"  [!!!] HIGH risk     : {high}")
    print(f"  [??]  MEDIUM risk   : {medium}")
    print(f"  [OK]  LOW risk      : {low}")
    print(f"  Vulnerable files    : {vulnerable}/{total} ({vulnerable/total*100:.1f}%)" if total > 0 else "")
    print(f"{'='*70}\n")

    # Save JSON report
    report_path = target_dir / "vulnerability_scan_report.json"
    report = {
        "target": str(target_dir.resolve()),
        "total_files": total,
        "vulnerable_files": vulnerable,
        "summary": {"high": high, "medium": medium, "low": low},
        "details": results,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"  Full report saved to: {report_path}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Secure data mining vulnerability predictor")
    subparsers = parser.add_subparsers(required=True)

    train_parser = subparsers.add_parser("train", help="Train vulnerability prediction model")
    train_parser.add_argument("--use-megavul", action="store_true", help="Use MegaVul dataset instead of the synthetic dataset")
    train_parser.add_argument("--use-codexglue", action="store_true", help="Use CodeXGLUE defect detection dataset")
    train_parser.add_argument("--use-combined", action="store_true", help="Combine all available datasets for training")
    train_parser.add_argument("--use-d2a", action="store_true", help="Use IBM D2A vulnerability dataset")
    train_parser.add_argument("--use-reveal", action="store_true", help="Use ReVeal (Chromium/Debian) vulnerability dataset")
    train_parser.add_argument("--use-vulberta", action="store_true", help="Use VulBERTa dataset")
    train_parser.add_argument("--use-owasp", action="store_true", help="Use generated OWASP Top 10 2025 dataset")
    train_parser.add_argument("--use-deep-learning", action="store_true", help="Use VulBERTa Deep Learning model instead of Random Forest")
    train_parser.add_argument("--tune", action="store_true", help="Perform hyperparameter tuning to find the best model configuration")
    train_parser.add_argument("--language", default="c_cpp", choices=["c_cpp", "java"], help="Language dataset to use for MegaVul")
    train_parser.set_defaults(func=train_command)

    predict_parser = subparsers.add_parser("predict", help="Predict vulnerability risk from JSON metrics")
    predict_parser.add_argument("--input", required=False, help="Path to JSON file with code metrics")
    predict_parser.add_argument("--raw-code", required=False, help="Path to a source code file (.c, .cpp, etc.) for syntactic prediction")
    predict_parser.add_argument("--shap-report", required=False, help="Path to output SHAP HTML report")
    predict_parser.set_defaults(func=predict_command)

    scan_parser = subparsers.add_parser("scan", help="Scan an entire project directory for vulnerabilities")
    scan_parser.add_argument("directory", help="Path to the project directory to scan")
    scan_parser.set_defaults(func=scan_command)

    args = parser.parse_args()
    try:
        args.func(args)
    except (FileNotFoundError, TypeError, ValueError, json.JSONDecodeError) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
