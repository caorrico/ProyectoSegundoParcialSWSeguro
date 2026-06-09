import math
from dataclasses import asdict, dataclass, fields
from typing import Any, ClassVar, Dict

from app.domain.value_objects import RiskLevel


@dataclass(frozen=True)
class CodeModuleMetrics:
    FEATURE_NAMES: ClassVar[tuple[str, ...]] = (
        "lines_of_code",
        "cyclomatic_complexity",
        "nesting_depth",
        "dependency_count",
        "deprecated_functions",
        "unsafe_patterns",
        "security_hotspots",
        "test_coverage",
        "recent_commits",
        "past_vulnerabilities",
    )

    lines_of_code: int
    cyclomatic_complexity: int
    nesting_depth: int
    dependency_count: int
    deprecated_functions: int
    unsafe_patterns: int
    security_hotspots: int
    test_coverage: float
    recent_commits: int
    past_vulnerabilities: int

    def __post_init__(self) -> None:
        for field in fields(self):
            field_name = field.name
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{field_name} must be numeric.")
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite.")
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative.")

        integer_fields = set(self.FEATURE_NAMES) - {"test_coverage"}
        for field_name in integer_fields:
            if not isinstance(getattr(self, field_name), int):
                raise TypeError(f"{field_name} must be an integer.")

        if self.test_coverage > 100:
            raise ValueError("test_coverage cannot be greater than 100.")
        if self.lines_of_code == 0:
            raise ValueError("lines_of_code must be greater than 0.")

    def to_feature_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VulnerabilityPrediction:
    is_vulnerable: bool
    risk_probability: float
    risk_level: RiskLevel
    recommendation: str

    def __post_init__(self) -> None:
        if not 0 <= self.risk_probability <= 1:
            raise ValueError("risk_probability must be between 0 and 1.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_vulnerable": self.is_vulnerable,
            "risk_probability": round(self.risk_probability, 4),
            "risk_level": self.risk_level.value,
            "recommendation": self.recommendation,
        }
