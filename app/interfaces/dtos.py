from typing import Any, Dict

from app.domain.entities import CodeModuleMetrics


class CodeModuleMetricsDTO:
    REQUIRED_FIELDS = set(CodeModuleMetrics.FEATURE_NAMES)

    @staticmethod
    def from_dict(payload: Dict[str, Any]) -> CodeModuleMetrics:
        if not isinstance(payload, dict):
            raise TypeError("Input JSON must be an object.")
        missing_fields = CodeModuleMetricsDTO.REQUIRED_FIELDS - set(payload.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {sorted(missing_fields)}")
        extra_fields = set(payload.keys()) - CodeModuleMetricsDTO.REQUIRED_FIELDS
        if extra_fields:
            raise ValueError(f"Unexpected fields: {sorted(extra_fields)}")
        return CodeModuleMetrics(**{field: payload[field] for field in CodeModuleMetricsDTO.REQUIRED_FIELDS})
