from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

from app.infrastructure.ml.ast_extractor import ASTFeatureExtractor


DANGEROUS_PATTERNS: dict[str, str] = {
    "eval": r"\beval\s*\(",
    "exec": r"\bexec\s*\(",
    "subprocess_shell": r"subprocess\.(run|Popen|call|check_output)\s*\([^)]*shell\s*=\s*True",
    "os_system": r"\bos\.system\s*\(|\bsystem\s*\(",
    "popen": r"\bpopen\s*\(",
    "sql_raw": r"(?i)(SELECT|INSERT|UPDATE|DELETE)\s+[^;\n]*(\+|\$\{|%s|format\()",
    "pickle": r"\bpickle\.(load|loads)\s*\(",
    "yaml_load": r"\byaml\.load\s*\(",
    "unsafe_c": r"\b(strcpy|strcat|gets|sprintf|memcpy)\s*\(",
    "hardcoded_secret": r"(?i)(password|secret|token|api[_-]?key)\s*=\s*['\"][^'\"]{6,}",
    "taint_source_scanf": r"\bscanf\s*\(",
    "taint_source_read": r"\bread\s*\([^)]*\)",
    "taint_source_argv": r"\bargv\b",
    "taint_source_getenv": r"\bgetenv\s*\(",
}

SANITIZATION_PATTERNS: dict[str, str] = {
    "parameterized_sql": r"execute\s*\([^)]*(\?|%s)",
    "escape": r"\b(escape|htmlspecialchars|sanitize|DOMPurify|bleach\.clean)\s*\(",
    "validation": r"\b(validate|is_valid|schema|pydantic|marshmallow)\b",
    "shell_false": r"subprocess\.(run|Popen|call|check_output)\s*\([^)]*shell\s*=\s*False",
}


class SecurityPatternFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract lightweight numeric security signals from raw source code."""

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        rows = []
        for code in X:
            if not isinstance(code, str):
                code = ""
            dangerous_counts = [
                len(re.findall(pattern, code)) for pattern in DANGEROUS_PATTERNS.values()
            ]
            sanitizer_counts = [
                len(re.findall(pattern, code)) for pattern in SANITIZATION_PATTERNS.values()
            ]
            tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+|==|!=|<=|>=|&&|\|\||[^\s]", code)
            lines = [line for line in code.splitlines() if line.strip()]
            imports = re.findall(
                r"(?m)^\s*(import|from\s+\S+\s+import|#include|using\s+|require\()", code
            )
            rows.append(
                [
                    len(lines),
                    len(tokens),
                    len(imports),
                    sum(dangerous_counts),
                    sum(sanitizer_counts),
                    max(0, sum(dangerous_counts) - sum(sanitizer_counts)),
                    *dangerous_counts,
                    *sanitizer_counts,
                ]
            )
        return np.array(rows, dtype=float)

    def get_feature_names_out(self, input_features=None):
        base_names = [
            "security_lines_of_code",
            "security_token_count",
            "security_import_count",
            "security_dangerous_total",
            "security_sanitization_total",
            "security_net_risk_patterns",
        ]
        dangerous_names = [f"security_dangerous_{name}" for name in DANGEROUS_PATTERNS]
        sanitizer_names = [f"security_sanitizer_{name}" for name in SANITIZATION_PATTERNS]
        return np.array([*base_names, *dangerous_names, *sanitizer_names])


@dataclass(frozen=True)
class CodeFeatureSummary:
    path: str
    language: str
    lines_of_code: int
    token_count: int
    import_count: int
    ast_node_count: int
    ast_max_depth: int
    ast_function_calls: int
    dangerous_call_count: int
    sanitization_count: int
    suspicious_pattern_count: int
    suspicious_patterns: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "language": self.language,
            "lines_of_code": self.lines_of_code,
            "token_count": self.token_count,
            "import_count": self.import_count,
            "ast_node_count": self.ast_node_count,
            "ast_max_depth": self.ast_max_depth,
            "ast_function_calls": self.ast_function_calls,
            "dangerous_call_count": self.dangerous_call_count,
            "sanitization_count": self.sanitization_count,
            "suspicious_pattern_count": self.suspicious_pattern_count,
            "suspicious_patterns": self.suspicious_patterns,
        }


def extract_code_features(code: str, path: str | Path = "<memory>") -> CodeFeatureSummary:
    path_text = str(path)
    ast_features = _safe_ast_features(code)
    suspicious = [
        name for name, pattern in DANGEROUS_PATTERNS.items() if re.search(pattern, code)
    ]
    sanitizers = [
        name for name, pattern in SANITIZATION_PATTERNS.items() if re.search(pattern, code)
    ]

    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+|==|!=|<=|>=|&&|\|\||[^\s]", code)
    import_count = len(
        re.findall(r"(?m)^\s*(import|from\s+\S+\s+import|#include|using\s+|require\()", code)
    )
    lines = [line for line in code.splitlines() if line.strip()]

    return CodeFeatureSummary(
        path=path_text,
        language=_detect_language(path_text, code),
        lines_of_code=len(lines),
        token_count=len(tokens),
        import_count=import_count,
        ast_node_count=int(ast_features[0]),
        ast_max_depth=int(ast_features[1]),
        ast_function_calls=int(ast_features[3]),
        dangerous_call_count=len(suspicious),
        sanitization_count=len(sanitizers),
        suspicious_pattern_count=len(suspicious),
        suspicious_patterns=suspicious,
    )


def _safe_ast_features(code: str) -> list[int]:
    try:
        values = ASTFeatureExtractor().transform([code])[0]
        return [int(value) for value in values.tolist()]
    except Exception:
        return [0, 0, 0, 0, 0, 0]


def _detect_language(path: str, code: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".c", ".h"}:
        return "c"
    if suffix in {".cc", ".cpp", ".cxx", ".hpp"}:
        return "cpp"
    if suffix == ".java" or re.search(r"\bpublic\s+class\b", code):
        return "java"
    if suffix == ".py":
        return "python"
    if suffix in {".js", ".ts"}:
        return suffix[1:]
    if suffix == ".go":
        return "go"
    if suffix == ".rs":
        return "rust"
    return "unknown"
