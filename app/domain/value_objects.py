from enum import Enum


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    @staticmethod
    def from_probability(probability: float) -> "RiskLevel":
        if probability < 0 or probability > 1:
            raise ValueError("Risk probability must be between 0 and 1.")
        if probability < 0.40:
            return RiskLevel.LOW
        if probability < 0.70:
            return RiskLevel.MEDIUM
        return RiskLevel.HIGH
