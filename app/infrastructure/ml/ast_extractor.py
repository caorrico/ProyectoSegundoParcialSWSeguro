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
    code_line: str = ""


SYNTAX_MESSAGE_MAP: dict[str, str] = {
    ";": "Missing semicolon",
    ")": "Missing closing parenthesis",
    "}": "Missing closing brace",
    "]": "Missing closing bracket",
    "{": "Missing opening brace",
    "(": "Missing opening parenthesis",
    "[": "Missing opening bracket",
    ":": "Missing colon",
    ",": "Missing comma",
    "=": "Missing assignment operator",
    "<": "Missing opening angle bracket",
    ">": "Missing closing angle bracket",
    "\"": "Unclosed string literal",
    "'": "Unclosed character literal",
}

NODE_NAME_MAP: dict[str, str] = {
    "else": "Missing 'else' clause",
    "compound_statement": "Missing code block '{ }'",
    "expression": "Missing expression statement",
    "statement": "Missing statement",
    "declaration": "Missing declaration",
    "parameter_list": "Missing parameter list",
    "argument_list": "Missing argument list",
    "initializer_list": "Missing initializer list",
    "function_definition": "Missing function definition",
    "template_parameter_list": "Missing template parameter list",
    "template_argument_list": "Missing template argument list",
    "enumerator_list": "Missing enumerator list",
    "switch_body": "Missing switch body '{ }'",
    "field_initializer_list": "Missing field initializer list",
    "base_class_clause": "Missing base class clause",
    "field_declaration": "Missing field declaration",
    "class_specifier": "Missing class definition '{ }'",
    "lambda_introducer": "Missing lambda introducer '[ ]'",
    "lambda_body": "Missing lambda body '{ }'",
    "type_descriptor": "Missing type name",
    "enumerator": "Missing enumerator",
    "abstract_array_declarator": "Missing array declarator",
    "dependent_name": "Missing dependent type name",
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

    lines = code.splitlines()

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
        _collect_syntax_errors(tree.root_node, syntax_errors, lines)
        return syntax_errors

    except Exception:
        return [SyntaxError(line=0, column=0, message="Failed to parse code (unknown parse error)")]


def _collect_syntax_errors(node: tree_sitter.Node, errors: list[SyntaxError], lines: list[str]) -> None:
    if node.type == "ERROR":
        row, col = node.start_point
        code_line = lines[row] if row < len(lines) else ""
        error_text = node.text.decode("utf8") if node.text else ""
        if not error_text:
            msg = "Syntax error"
        elif col == 0 and len(error_text) >= len(code_line):
            msg = "Parse error at start of line - check for unclosed strings, comments, or braces"
        else:
            display_text = error_text.replace("\n", " ").replace("\r", " ")[:30]
            if len(error_text) > 30:
                display_text += "..."
            msg = f"Unexpected token '{display_text}'"
        errors.append(SyntaxError(line=row + 1, column=col, message=msg, code_line=code_line))
    if node.is_missing:
        row, col = node.start_point
        token = node.type
        code_line = lines[row] if row < len(lines) else ""
        msg = SYNTAX_MESSAGE_MAP.get(token) or NODE_NAME_MAP.get(token) or _friendly_node_name(token)
        errors.append(SyntaxError(line=row + 1, column=col, message=msg, code_line=code_line))
    for child in node.children:
        _collect_syntax_errors(child, errors, lines)


def _friendly_node_name(name: str) -> str:
    readable = name.replace("_", " ")
    return f"Missing: {readable}"


def _suffix(filename: str) -> str:
    idx = filename.rfind(".")
    return filename[idx:].lower() if idx != -1 else ""
