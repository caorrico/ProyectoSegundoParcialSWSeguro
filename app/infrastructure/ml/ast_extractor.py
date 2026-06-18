import numpy as np
import re
import tree_sitter
import tree_sitter_cpp
import tree_sitter_java
from sklearn.base import BaseEstimator, TransformerMixin

class ASTFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
<<<<<<< HEAD
        cpp_parser = self._build_parser(tree_sitter_cpp.language)
        java_parser = self._build_parser(tree_sitter_java.language)
=======
        # Create Language objects with (ptr, name)
        cpp_lang = tree_sitter.Language(tree_sitter_cpp.language(), "cpp")
        java_lang = tree_sitter.Language(tree_sitter_java.language(), "java")
        
        # Create parsers and set languages
        cpp_parser = tree_sitter.Parser()
        cpp_parser.set_language(cpp_lang)
        java_parser = tree_sitter.Parser()
        java_parser.set_language(java_lang)
>>>>>>> 65ec38926cbd8ebcd48a7bd65f8f809adddfe04e

        features = []
        for code in X:
            if not isinstance(code, str):
                code = ""

            # Simple heuristic to detect Java
            if re.search(r'\b(public\s+class|import\s+java)\b', code):
                parser = java_parser
            else:
                parser = cpp_parser

            tree = parser.parse(bytes(code, "utf8"))

            stats = self._extract_stats(tree.root_node)
            features.append([
                stats.get("node_count", 0),
                stats.get("max_depth", 0),
                stats.get("pointer_ops", 0),
                stats.get("function_calls", 0),
                stats.get("loops", 0),
                stats.get("if_statements", 0)
            ])

        return np.array(features)

    def _build_parser(self, language_factory):
        language = tree_sitter.Language(language_factory())
        parser = tree_sitter.Parser()
        if hasattr(parser, "set_language"):
            parser.set_language(language)
        else:
            parser.language = language
        return parser

    def _extract_stats(self, root_node):
        stats = {
            "node_count": 0,
            "max_depth": 0,
            "pointer_ops": 0,
            "function_calls": 0,
            "loops": 0,
            "if_statements": 0
        }

        # Iterative traversal using a stack
        stack = [(root_node, 0)]
        while stack:
            node, depth = stack.pop()

            stats["node_count"] += 1
            stats["max_depth"] = max(stats["max_depth"], depth)

            node_type = node.type

            # Pointers/References in C/C++
            if node_type in ["pointer_declarator", "reference_declarator", "pointer_expression"]:
                stats["pointer_ops"] += 1

            # Function calls
            if node_type in ["call_expression", "method_invocation"]:
                stats["function_calls"] += 1

            # Loops
            if node_type in ["while_statement", "for_statement", "do_statement"]:
                stats["loops"] += 1

            # Conditionals
            if node_type in ["if_statement"]:
                stats["if_statements"] += 1

            for child in node.children:
                stack.append((child, depth + 1))

        return stats

    def get_feature_names_out(self, input_features=None):
        return np.array([
            "ast_node_count",
            "ast_max_depth",
            "ast_pointer_ops",
            "ast_function_calls",
            "ast_loops",
            "ast_if_statements"
        ])
