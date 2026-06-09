from pathlib import Path
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.shared.settings import settings  # noqa: E402


def generate_dataset(rows: int = 1500, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)

    lines_of_code = rng.integers(50, 2500, rows)
    cyclomatic_complexity = rng.integers(1, 45, rows)
    nesting_depth = rng.integers(1, 12, rows)
    dependency_count = rng.integers(0, 40, rows)
    deprecated_functions = rng.integers(0, 8, rows)
    unsafe_patterns = rng.integers(0, 12, rows)
    security_hotspots = rng.integers(0, 18, rows)
    test_coverage = rng.uniform(5, 100, rows).round(2)
    recent_commits = rng.integers(1, 80, rows)
    past_vulnerabilities = rng.integers(0, 6, rows)

    risk_score = (
        (lines_of_code / 2500) * 0.10
        + (cyclomatic_complexity / 45) * 0.18
        + (nesting_depth / 12) * 0.10
        + (dependency_count / 40) * 0.08
        + (deprecated_functions / 8) * 0.14
        + (unsafe_patterns / 12) * 0.20
        + (security_hotspots / 18) * 0.12
        + ((100 - test_coverage) / 100) * 0.12
        + (recent_commits / 80) * 0.04
        + (past_vulnerabilities / 6) * 0.16
    )
    noise = rng.normal(0, 0.06, rows)
    is_vulnerable = ((risk_score + noise) >= 0.48).astype(int)

    return pd.DataFrame(
        {
            "lines_of_code": lines_of_code,
            "cyclomatic_complexity": cyclomatic_complexity,
            "nesting_depth": nesting_depth,
            "dependency_count": dependency_count,
            "deprecated_functions": deprecated_functions,
            "unsafe_patterns": unsafe_patterns,
            "security_hotspots": security_hotspots,
            "test_coverage": test_coverage,
            "recent_commits": recent_commits,
            "past_vulnerabilities": past_vulnerabilities,
            "is_vulnerable": is_vulnerable,
        }
    )


def main() -> None:
    dataset = generate_dataset()
    settings.dataset_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(settings.dataset_path, index=False)
    print(f"Dataset generated at: {settings.dataset_path}")
    print(dataset["is_vulnerable"].value_counts().to_dict())


if __name__ == "__main__":
    main()
