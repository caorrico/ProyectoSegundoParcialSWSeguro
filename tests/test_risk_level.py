import pytest

from app.domain.value_objects import RiskLevel


def test_low_risk_level() -> None:
    assert RiskLevel.from_probability(0.20) == RiskLevel.LOW
    assert RiskLevel.from_probability(0.3999) == RiskLevel.LOW


def test_medium_risk_level() -> None:
    assert RiskLevel.from_probability(0.40) == RiskLevel.MEDIUM
    assert RiskLevel.from_probability(0.55) == RiskLevel.MEDIUM
    assert RiskLevel.from_probability(0.6999) == RiskLevel.MEDIUM


def test_high_risk_level() -> None:
    assert RiskLevel.from_probability(0.70) == RiskLevel.HIGH


def test_invalid_probability() -> None:
    with pytest.raises(ValueError):
        RiskLevel.from_probability(1.20)
