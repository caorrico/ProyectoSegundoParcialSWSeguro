from sklearn.base import BaseEstimator, TransformerMixin
from scipy.sparse import csr_matrix
import numpy as np
import re
import tree_sitter
import tree_sitter_cpp
import tree_sitter_java

class RobustASTFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self):
        self._cpp_parser = None
        self._java_parser = None
        self._unavailable = False
    
    def _init_parsers(self):
        if self._cpp_parser is None and not self._unavailable:
            try:
                cpp_lang = tree_sitter.Language(tree_sitter_cpp.language())
                java_lang = tree_sitter.Language(tree_sitter_java.language())
                self._cpp_parser = tree_sitter.Parser(cpp_lang)
                self._java_parser = tree_sitter.Parser(java_lang)
            except Exception:
                self._unavailable = True
    
    def fit(self, X, y=None): return self
    
    def transform(self, X, y=None):
        self._init_parsers()
        features = []
        for code in X:
            if not isinstance(code, str) or not code.strip():
                features.append([0]*6); continue
            
            if self._unavailable:
                features.append([len(code.split()), 0, 0, 0, 0, 0])
            else:
                try:
                    parser = self._java_parser if re.search(r'\b(public\s+class|import\s+java)\b', code) else self._cpp_parser
                    tree = parser.parse(bytes(code, 'utf8'))
                    stats = self._extract_stats(tree.root_node)
                    features.append([stats['node_count'], stats['max_depth'], stats['pointer_ops'], stats['function_calls'], stats['loops'], stats['if_statements']])
                except:
                    features.append([len(code.split()), 0, 0, 0, 0, 0])
        return csr_matrix(np.array(features))

    def _extract_stats(self, root_node):
        stats = {'node_count': 0, 'max_depth': 0, 'pointer_ops': 0, 'function_calls': 0, 'loops': 0, 'if_statements': 0}
        stack = [(root_node, 0)]
        while stack:
            node, depth = stack.pop()
            stats['node_count'] += 1
            stats['max_depth'] = max(stats['max_depth'], depth)
            if node.type in ['pointer_declarator', 'reference_declarator', 'pointer_expression']: stats['pointer_ops'] += 1
            if node.type in ['call_expression', 'method_invocation']: stats['function_calls'] += 1
            if node.type in ['while_statement', 'for_statement', 'do_statement']: stats['loops'] += 1
            if node.type in ['if_statement']: stats['if_statements'] += 1
            for child in node.children: stack.append((child, depth + 1))
        return stats

class AdvancedTaintExtractor(BaseEstimator, TransformerMixin):
    SOURCES = [r'\$_GET', r'\$_POST', r'\bscanf\s*\(', r'\bread\s*\(', r'\bargv', r'\bgetenv']
    SINKS = [r'\bstrcpy\s*\(', r'\bexec\s*\(', r'\beval\s*\(', r'\bsystem\s*\(', r'SELECT.*FROM', r'\bmemcpy\s*\(']
    
    def fit(self, X, y=None): return self
    
    def transform(self, X, y=None):
        features = []
        for code in X:
            if not isinstance(code, str): code = ''
            has_source = any(re.search(p, code) for p in self.SOURCES)
            has_sink = any(re.search(p, code) for p in self.SINKS)
            sanitizers = len(re.findall(r'\bescape\b|\bvalidate\b|\bfilter_var\b', code, re.IGNORECASE))
            features.append([int(has_source), int(has_sink), int(has_source and has_sink), sanitizers])
        return csr_matrix(np.array(features, dtype=np.float64))

class EnhancedCodeMetrics(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): return self
    def transform(self, X, y=None):
        features = []
        for code in X:
            if not isinstance(code, str): code = ''
            lines = len(code.split('\n'))
            chars = len(code)
            pointers = len(re.findall(r'[*&]', code))
            funcs = len(re.findall(r'\w+\s*\(', code))
            features.append([lines, chars, pointers, funcs])
        return csr_matrix(np.array(features, dtype=np.float64))
