from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.application.use_cases.predict_vulnerability import CodeAnalyzer  # noqa: E402
from app.domain.entities import RawCodeModule  # noqa: E402
from app.infrastructure.ml.code_feature_extractor import extract_code_features  # noqa: E402
from app.infrastructure.ml.random_forest_predictor import RandomForestPredictor  # noqa: E402
from app.shared.settings import settings  # noqa: E402


SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hpp",
    ".java",
    ".py",
    ".js",
    ".ts",
    ".go",
    ".rs",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze PR source changes with the trained ML model.")
    parser.add_argument("--base-ref", default="origin/test", help="Base git ref for diff detection")
    parser.add_argument("--head-ref", default="HEAD", help="Head git ref for diff detection")
    parser.add_argument("--changed-files", help="Text file with one changed path per line")
    parser.add_argument("--output", default="reports/pr_security_scan.json", help="JSON report path")
    parser.add_argument("--threshold", type=float, default=0.50, help="Vulnerability probability threshold")
    parser.add_argument("--allow-missing-model", action="store_true", help="Return UNKNOWN instead of failing if model is missing")
    args = parser.parse_args()

    try:
        files = _load_changed_files(args.changed_files, args.base_ref, args.head_ref)
        report = analyze_files(files, args.threshold, args.allow_missing_model)
    except Exception as error:
        report = {
            "status": "ERROR",
            "probability": 0.0,
            "details": str(error),
            "files": [],
            "model_path": str(settings.model_path),
        }
        _write_report(report, Path(args.output))
        print(json.dumps(report, indent=2))
        sys.exit(2)

    _write_report(report, Path(args.output))
    print(json.dumps(report, indent=2))
    if report["status"] == "VULNERABLE":
        sys.exit(1)


def analyze_files(
    files: list[Path], threshold: float = 0.50, allow_missing_model: bool = False
) -> dict[str, Any]:
    if not settings.model_path.exists():
        if allow_missing_model:
            return {
                "status": "UNKNOWN",
                "probability": 0.0,
                "details": f"Model not found at {settings.model_path}",
                "files": [],
                "model_path": str(settings.model_path),
            }
        raise FileNotFoundError(
            f"Model not found at {settings.model_path}. Train it before scanning."
        )

    predictor = RandomForestPredictor(settings.model_path)
    analyzed: list[dict[str, Any]] = []
    max_probability = 0.0
    vulnerable_count = 0

    for path in files:
        if not _is_source_file(path) or not path.exists():
            continue
        code = path.read_text(encoding="utf-8", errors="replace")
        if not code.strip():
            continue

        prediction, probability = predictor.predict(RawCodeModule(code))
        probability = round(float(probability), 4)
        is_vulnerable = prediction or probability >= threshold
        max_probability = max(max_probability, probability)
        if is_vulnerable:
            vulnerable_count += 1

        vulnerability_types, cwe_ids, recommendations = CodeAnalyzer.analyze_raw_code(code)
        feature_summary = extract_code_features(code, path)
        analyzed.append(
            {
                "path": str(path.as_posix()),
                "status": "VULNERABLE" if is_vulnerable else "SAFE",
                "probability": probability,
                "risk_level": _risk_level(probability),
                "vulnerability_types": vulnerability_types,
                "cwe_ids": cwe_ids,
                "recommendations": recommendations,
                "features": feature_summary.to_dict(),
            }
        )

    status = "VULNERABLE" if vulnerable_count else "SAFE"
    return {
        "status": status,
        "probability": round(max_probability, 4),
        "details": (
            f"{vulnerable_count} vulnerable file(s) found out of {len(analyzed)} analyzed."
            if analyzed
            else "No relevant source files were changed."
        ),
        "files": analyzed,
        "model_path": str(settings.model_path),
    }


def _load_changed_files(changed_files: str | None, base_ref: str, head_ref: str) -> list[Path]:
    if changed_files:
        path = Path(changed_files)
        return [Path(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    command = ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return [Path(line.strip()) for line in result.stdout.splitlines() if line.strip()]


def _is_source_file(path: Path) -> bool:
    return path.suffix.lower() in SOURCE_EXTENSIONS


def _risk_level(probability: float) -> str:
    if probability >= 0.70:
        return "HIGH"
    if probability >= 0.40:
        return "MEDIUM"
    return "LOW"


def _write_report(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
