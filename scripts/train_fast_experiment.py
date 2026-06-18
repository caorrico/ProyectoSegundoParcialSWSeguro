#!/usr/bin/env python3
"""
Experimento de entrenamiento rápido con un subset pequeño de datos.
Basado en el notebook entrenamiento_avanzado.ipynb.
"""
import sys
import json
import re
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.base import BaseEstimator, TransformerMixin
from scipy.sparse import csr_matrix

# Agregar project root al path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# === CONFIGURACIÓN ===
PRUEBA_LIMIT = 200  # Muy pequeño para que sea instantáneo
RANDOM_STATE = 42

# === EXTRACTORES DE FEATURES (Copiados del notebook) ===

class SecurityFeatureExtractor(BaseEstimator, TransformerMixin):
    DANGEROUS_FUNCTIONS = {
        'buffer_overflow': [r'\bstrcpy\s*\(', r'\bstrcat\s*\(', r'\bsprintf\s*\(', r'\bgets\s*\('],
        'injection': [r'\bexec\s*\(', r'\beval\s*\(', r'\bsystem\s*\(', r'SELECT.*FROM'],
        'memory_mgmt': [r'\bmalloc\s*\(', r'\bfree\s*\(', r'\bnew\s+\w+'],
        'crypto_weak': [r'\bMD5\b', r'\bSHA1\b', r'\brand\s*\('],
    }
    
    SAFE_PATTERNS = [r'\bstrncpy\s*\(', r'\bsnprintf\s*\(', r'\bsanitize', r'\bvalidate']
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X, y=None):
        features = []
        for code in X:
            if not isinstance(code, str):
                code = ''
            row = []
            for category, patterns in self.DANGEROUS_FUNCTIONS.items():
                count = sum(len(re.findall(p, code, re.IGNORECASE)) for p in patterns)
                row.append(count)
            safe_count = sum(len(re.findall(p, code, re.IGNORECASE)) for p in self.SAFE_PATTERNS)
            row.append(safe_count)
            row.append(len(code))
            row.append(len(code.split('\n')))
            features.append(row)
        return csr_matrix(np.array(features, dtype=np.float64))
    
    def get_feature_names_out(self, input_features=None):
        names = [f'sec_{cat}' for cat in self.DANGEROUS_FUNCTIONS.keys()]
        names += ['sec_safe_patterns', 'code_length', 'code_lines']
        return np.array(names)

class RobustASTFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self):
        self._cpp_parser = None
        self._java_parser = None
    
    def _init_parsers(self):
        if self._cpp_parser is None:
            try:
                import tree_sitter
                import tree_sitter_cpp
                import tree_sitter_java
                cpp_lang = tree_sitter.Language(tree_sitter_cpp.language())
                java_lang = tree_sitter.Language(tree_sitter_java.language())
                self._cpp_parser = tree_sitter.Parser()
                self._cpp_parser.set_language(cpp_lang)
                self._java_parser = tree_sitter.Parser()
                self._java_parser.set_language(java_lang)
            except Exception:
                self._cpp_parser = 'unavailable'
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X, y=None):
        self._init_parsers()
        features = []
        for code in X:
            if self._cpp_parser == 'unavailable' or not isinstance(code, str):
                features.append([0, 0, 0, 0])
            else:
                try:
                    parser = self._java_parser if 'public class' in code else self._cpp_parser
                    tree = parser.parse(bytes(code, 'utf8'))
                    # Simplified stats for speed
                    node_count = 0
                    stack = [tree.root_node]
                    while stack:
                        node = stack.pop()
                        node_count += 1
                        for child in node.children:
                            stack.append(child)
                    features.append([node_count, 0, 0, 0])
                except Exception:
                    features.append([0, 0, 0, 0])
        return csr_matrix(np.array(features))
    
    def get_feature_names_out(self, input_features=None):
        return np.array(['ast_nodes', 'ast_depth_placeholder', 'ast_calls_placeholder', 'ast_loops_placeholder'])

class LanguageFeatureExtractor(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    def transform(self, X, y=None):
        features = []
        for code in X:
            if not isinstance(code, str):
                code = ''
            is_java = 1 if 'public class' in code or 'import java' in code else 0
            is_cpp = 1 if '#include' in code or 'std::' in code else 0
            features.append([is_java, is_cpp])
        return csr_matrix(np.array(features))
    def get_feature_names_out(self, input_features=None):
        return np.array(['lang_java', 'lang_cpp'])

# === FUNCIONES DE CARGA ===

def load_jsonl(path, code_field='func', label_field='target', limit=None):
    data = []
    if not Path(path).exists():
        return data
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            try:
                item = json.loads(line)
                code = item.get(code_field) or item.get('code') or item.get('functionSource') or ''
                label = item.get(label_field) or item.get('label') or 0
                if code and len(code) > 10:
                    data.append({'raw_code': code, 'is_vulnerable': int(label)})
            except Exception:
                continue
    return data

# === MAIN ===

def main():
    print(f"🚀 Iniciando experimento rápido (Subset de {PRUEBA_LIMIT} muestras por fuente)")
    
    all_data = []
    
    # Cargar subsets de algunos datasets
    datasets = [
        ('codexglue', 'data/codexglue/train.jsonl', 'func', 'target'),
        ('d2a', 'data/d2a/train.jsonl', 'functionSource', 'label'),
        ('reveal', 'data/reveal/train.jsonl', 'code', 'label'),
        ('owasp', 'data/owasp2025/train.jsonl', 'raw_code', 'is_vulnerable'),
    ]
    
    for name, path, cf, lf in datasets:
        p = PROJECT_ROOT / path
        if p.exists():
            data = load_jsonl(p, code_field=cf, label_field=lf, limit=PRUEBA_LIMIT)
            print(f"  ✅ {name}: {len(data)} muestras")
            all_data.extend(data)
    
    if not all_data:
        print("❌ No se encontraron datos. Verifica las rutas.")
        return

    df = pd.DataFrame(all_data)
    # Convert to list first to avoid any weird pandas/arrow issues
    X = np.array(df['raw_code'].tolist())
    y = np.array(df['is_vulnerable'].tolist())
    
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    
    print(f"\n📊 Dataset listo: {len(X_train_raw)} train, {len(X_test_raw)} test")
    
    # Pipeline
    print("🔧 Construyendo pipeline de features...")
    feature_pipeline = FeatureUnion([
        ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
        ('ast', RobustASTFeatureExtractor()),
        ('security', SecurityFeatureExtractor()),
        ('language', LanguageFeatureExtractor()),
    ])
    
    start = time.time()
    print("   Extrayendo features (fit_transform)...")
    X_train = feature_pipeline.fit_transform(X_train_raw)
    X_test = feature_pipeline.transform(X_test_raw)
    print(f"   ✅ Features extraídas en {time.time() - start:.2f}s")
    print(f"   Shape: {X_train.shape}")
    
    # Modelo
    print("\n🌲 Entrenando Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=RANDOM_STATE)
    rf.fit(X_train, y_train)
    
    # Evaluación
    preds = rf.predict(X_test)
    probas = rf.predict_proba(X_test)[:, 1]
    
    print("\n" + "="*30)
    print("  RESULTADOS EXPERIMENTO")
    print("="*30)
    print(f"  Accuracy:  {accuracy_score(y_test, preds):.4f}")
    print(f"  Precision: {precision_score(y_test, preds):.4f}")
    print(f"  Recall:    {recall_score(y_test, preds):.4f}")
    print(f"  F1 Score:  {f1_score(y_test, preds):.4f}")
    print(f"  ROC AUC:   {roc_auc_score(y_test, probas):.4f}")
    print("="*30)

if __name__ == "__main__":
    main()
