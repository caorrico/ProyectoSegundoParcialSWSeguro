import numpy as np
import tree_sitter
import tree_sitter_cpp
import tree_sitter_java
from sklearn.base import BaseEstimator, TransformerMixin
import re

class ASTFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        cpp_lang = tree_sitter.Language(tree_sitter_cpp.language())
        java_lang = tree_sitter.Language(tree_sitter_java.language())
        cpp_parser = tree_sitter.Parser(cpp_lang)
        java_parser = tree_sitter.Parser(java_lang)

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

    def _extract_stats(self, node):
        stats = {
            "node_count": 0,
            "max_depth": 0,
            "pointer_ops": 0,
            "function_calls": 0,
            "loops": 0,
            "if_statements": 0
        }
        self._traverse(node, 0, stats)
        return stats

    def _traverse(self, node, current_depth, stats):
        stats["node_count"] += 1
        stats["max_depth"] = max(stats["max_depth"], current_depth)

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
            self._traverse(child, current_depth + 1, stats)

    def get_feature_names_out(self, input_features=None):
        return np.array([
            "ast_node_count",
            "ast_max_depth",
            "ast_pointer_ops",
            "ast_function_calls",
            "ast_loops",
            "ast_if_statements"
        ])
