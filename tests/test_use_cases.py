from app.application.use_cases.predict_vulnerability import PredictVulnerabilityUseCase
from app.domain.entities import CodeModuleMetrics
from app.domain.value_objects import RiskLevel


class StubPredictor:
    def predict(self, metrics: CodeModuleMetrics) -> tuple[bool, float]:
        return True, 0.82


def test_prediction_use_case_builds_expected_result() -> None:
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

    prediction = PredictVulnerabilityUseCase(StubPredictor()).execute(metrics)

    assert prediction.is_vulnerable is True
    assert prediction.risk_probability == 0.82
    assert prediction.risk_level == RiskLevel.HIGH
