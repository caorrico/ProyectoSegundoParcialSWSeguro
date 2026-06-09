import pytest

from app.interfaces.dtos import CodeModuleMetricsDTO


VALID_PAYLOAD = {
    "lines_of_code": 100,
    "cyclomatic_complexity": 5,
    "nesting_depth": 2,
    "dependency_count": 3,
    "deprecated_functions": 0,
    "unsafe_patterns": 1,
    "security_hotspots": 2,
    "test_coverage": 80.0,
    "recent_commits": 4,
    "past_vulnerabilities": 0,
}


def test_dto_rejects_missing_fields() -> None:
    payload = {key: value for key, value in VALID_PAYLOAD.items() if key != "lines_of_code"}

    with pytest.raises(ValueError, match="Missing required fields"):
        CodeModuleMetricsDTO.from_dict(payload)


def test_dto_rejects_unexpected_fields() -> None:
    payload = {**VALID_PAYLOAD, "unknown_metric": 1}

    with pytest.raises(ValueError, match="Unexpected fields"):
        CodeModuleMetricsDTO.from_dict(payload)
