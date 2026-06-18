import re
from dataclasses import dataclass

import numpy as np
import tree_sitter
import tree_sitter_cpp
import tree_sitter_java
from sklearn.base import BaseEstimator, TransformerMixin


@dataclass
class SyntaxError:
    line: int
    column: int
    message: str


SYNTAX_MESSAGE_MAP: dict[str, str] = {
    ";": "Missing semicolon",
    ")": "Missing closing parenthesis",
    "}": "Missing closing brace",
    "]": "Missing closing bracket",
}


class ASTFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self):
        self._cpp_parser = None
        self._java_parser = None

    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop("_cpp_parser", None)
        state.pop("_java_parser", None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._cpp_parser = None
        self._java_parser = None

    def fit(self, X, y=None):
        return self

    def _create_language(self, language_capsule):
        try:
            return tree_sitter.Language(language_capsule)
        except TypeError:
            return tree_sitter.Language(language_capsule, name='')

    def _ensure_parsers(self):
        if self._cpp_parser is None:
            cpp_lang = self._create_language(tree_sitter_cpp.language())
            self._cpp_parser = tree_sitter.Parser(cpp_lang)
        if self._java_parser is None:
            java_lang = self._create_language(tree_sitter_java.language())
            self._java_parser = tree_sitter.Parser(java_lang)

    def transform(self, X, y=None):
        self._ensure_parsers()

        features = []
        for code in X:
            if not isinstance(code, str) or not code.strip():
                features.append([0, 0, 0, 0, 0, 0])
                continue

            if re.search(r"\b(public\s+class|import\s+java)\b", code):
                parser = self._java_parser
            else:
                parser = self._cpp_parser

            try:
                tree = parser.parse(bytes(code, "utf8"))
                stats = self._extract_stats(tree.root_node)
            except Exception:
                stats = {"node_count": 0, "max_depth": 0, "pointer_ops": 0, "function_calls": 0, "loops": 0, "if_statements": 0}

            features.append(
                [
                    stats.get("node_count", 0),
                    stats.get("max_depth", 0),
                    stats.get("pointer_ops", 0),
                    stats.get("function_calls", 0),
                    stats.get("loops", 0),
                    stats.get("if_statements", 0),
                ]
            )

        return np.array(features)

    def _extract_stats(self, root_node):
        stats = {
            "node_count": 0,
            "max_depth": 0,
            "pointer_ops": 0,
            "function_calls": 0,
            "loops": 0,
            "if_statements": 0,
        }

        stack = [(root_node, 0)]
        while stack:
            node, depth = stack.pop()
            stats["node_count"] += 1
            stats["max_depth"] = max(stats["max_depth"], depth)
            node_type = node.type

            if node_type in ["pointer_declarator", "reference_declarator", "pointer_expression"]:
                stats["pointer_ops"] += 1
            if node_type in ["call_expression", "method_invocation"]:
                stats["function_calls"] += 1
            if node_type in ["while_statement", "for_statement", "do_statement"]:
                stats["loops"] += 1
            if node_type in ["if_statement"]:
                stats["if_statements"] += 1

            for child in node.children:
                stack.append((child, depth + 1))

        return stats

    def get_feature_names_out(self, input_features=None):
        return np.array(
            [
                "ast_node_count",
                "ast_max_depth",
                "ast_pointer_ops",
                "ast_function_calls",
                "ast_loops",
                "ast_if_statements",
            ]
        )


def validate_code_syntax(code: str, filename: str = "") -> list[SyntaxError]:
    suffix = _suffix(filename)
    if suffix in {".py", ".js", ".ts", ".go", ".rs"}:
        return []

    try:
        if suffix in {".java"} or re.search(r"\b(public\s+class|import\s+java)\b", code):
            lang = tree_sitter.Language(tree_sitter_java.language())
        else:
            lang = tree_sitter.Language(tree_sitter_cpp.language())

        parser = tree_sitter.Parser(lang)
        tree = parser.parse(bytes(code, "utf8"))

        if not tree.root_node.has_error:
            return []

        syntax_errors: list[SyntaxError] = []
        _collect_syntax_errors(tree.root_node, syntax_errors)
        return syntax_errors

    except Exception:
        return [SyntaxError(line=0, column=0, message="Failed to parse code (unknown parse error)")]


def _collect_syntax_errors(node: tree_sitter.Node, errors: list[SyntaxError]) -> None:
    if node.type == "ERROR":
        row, col = node.start_point
        errors.append(SyntaxError(line=row + 1, column=col, message="Syntax error"))
    if node.is_missing:
        row, col = node.start_point
        token = node.type
        msg = SYNTAX_MESSAGE_MAP.get(token, f"Missing token '{token}'")
        errors.append(SyntaxError(line=row + 1, column=col, message=msg))
    for child in node.children:
        _collect_syntax_errors(child, errors)


def _suffix(filename: str) -> str:
    idx = filename.rfind(".")
    return filename[idx:].lower() if idx != -1 else ""
