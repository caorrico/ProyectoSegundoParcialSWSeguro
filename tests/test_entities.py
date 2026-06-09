import pytest

from app.domain.entities import CodeModuleMetrics


def test_create_valid_code_module_metrics() -> None:
    metrics = CodeModuleMetrics(
        lines_of_code=100,
        cyclomatic_complexity=5,
        nesting_depth=2,
        dependency_count=3,
        deprecated_functions=0,
        unsafe_patterns=1,
        security_hotspots=2,
        test_coverage=80.0,
        recent_commits=4,
        past_vulnerabilities=0,
    )

    assert metrics.lines_of_code == 100
    assert metrics.test_coverage == 80.0


def test_negative_metrics_are_invalid() -> None:
    with pytest.raises(ValueError):
        CodeModuleMetrics(
            lines_of_code=-1,
            cyclomatic_complexity=5,
            nesting_depth=2,
            dependency_count=3,
            deprecated_functions=0,
            unsafe_patterns=1,
            security_hotspots=2,
            test_coverage=80.0,
            recent_commits=4,
            past_vulnerabilities=0,
        )


def test_coverage_greater_than_100_is_invalid() -> None:
    with pytest.raises(ValueError):
        CodeModuleMetrics(
            lines_of_code=100,
            cyclomatic_complexity=5,
            nesting_depth=2,
            dependency_count=3,
            deprecated_functions=0,
            unsafe_patterns=1,
            security_hotspots=2,
            test_coverage=120.0,
            recent_commits=4,
            past_vulnerabilities=0,
        )


@pytest.mark.parametrize("invalid_value", ["100", True, float("nan"), float("inf")])
def test_invalid_numeric_values_are_rejected(invalid_value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        CodeModuleMetrics(
            lines_of_code=invalid_value,  # type: ignore[arg-type]
            cyclomatic_complexity=5,
            nesting_depth=2,
            dependency_count=3,
            deprecated_functions=0,
            unsafe_patterns=1,
            security_hotspots=2,
            test_coverage=80.0,
            recent_commits=4,
            past_vulnerabilities=0,
        )
