#!/usr/bin/env python3
"""
Pipeline final de alto rendimiento para alcanzar >82% Accuracy.
Consolidado para evitar errores de importación y guardar gráficos.
"""
import sys
import random
import re
import joblib
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline as SkPipeline
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay, roc_curve, precision_recall_curve, roc_auc_score
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import csr_matrix
from xgboost import XGBClassifier

# Agregar project root al path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.infrastructure.repositories.combined_dataset_repository import CombinedDatasetRepository

# === EXTRACTORES DE ALTA FIDELIDAD ===

class RobustASTFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self):
        self._cpp_parser = None
        self._java_parser = None
        self._unavailable = False
    
    def _init_parsers(self):
        if self._cpp_parser is None and not self._unavailable:
            try:
                import tree_sitter
                import tree_sitter_cpp
                import tree_sitter_java
                cpp_lang = tree_sitter.Language(tree_sitter_cpp.language())
                java_lang = tree_sitter.Language(tree_sitter_java.language())
                self._cpp_parser = tree_sitter.Parser(cpp_lang)
                self._java_parser = tree_sitter.Parser(java_lang)
            except Exception as e:
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

# === PIPELINE FINAL ===

def run_final_pipeline():
    print("=" * 80)
    print("  ENTRENAMIENTO DE MÁXIMA PRECISIÓN (Target >82%)")
    print("=" * 80)

    # 1. Cargar Dataset (CVEFixes)
    repo = CombinedDatasetRepository(limit_per_source=None)
    all_data = repo.load()
    cve_data = [d for d in all_data if d.get('source') == 'cvefixes']
    
    # Balancear
    vuln = [d for d in cve_data if d['is_vulnerable']]
    safe = [d for d in cve_data if not d['is_vulnerable']]
    count = min(len(vuln), len(safe), 500) # 1000 muestras totales para prueba rápida

    samples = random.sample(vuln, count) + random.sample(safe, count)
    random.shuffle(samples)
    
    X = [s['raw_code'] for s in samples]
    y = np.array([s['is_vulnerable'] for s in samples])
    
    # 2. Split
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)
    
    # 3. Feature Engineering
    feature_pipeline = FeatureUnion([
        ('tfidf_word', TfidfVectorizer(max_features=5000, ngram_range=(1, 3))),
        ('tfidf_char', TfidfVectorizer(max_features=3000, ngram_range=(3, 6), analyzer='char')),
        ('ast', RobustASTFeatureExtractor()),
        ('metrics', EnhancedCodeMetrics()),
    ])

    print("   🔧 Extrayendo features...")
    X_train_feat = feature_pipeline.fit_transform(X_train)
    X_val_feat = feature_pipeline.transform(X_val)
    X_test_feat = feature_pipeline.transform(X_test)

    # 4. XGBoost con parámetros optimizados
    model = XGBClassifier(
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=12,
        min_child_weight=1,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=42,
        eval_metric='error',
        early_stopping_rounds=100
    )
    
    print("   🏋️ Entrenando...")
    model.fit(X_train_feat, y_train, eval_set=[(X_val_feat, y_val)], verbose=False)
    
    # 5. Evaluación Final y Generación de Gráficos
    preds = model.predict(X_test_feat)
    probs = model.predict_proba(X_test_feat)[:, 1]
    test_acc = accuracy_score(y_test, preds)
    
    print(f"\n   🎯 Accuracy Final: {test_acc:.2%}")
    
    REPORT_DIR = PROJECT_ROOT / 'reports'
    REPORT_DIR.mkdir(exist_ok=True)
    
    # Matriz de Confusión
    cm = confusion_matrix(y_test, preds)
    ConfusionMatrixDisplay(cm, display_labels=['Safe', 'Vuln']).plot(cmap='Blues')
    plt.title('Matriz de Confusión')
    plt.savefig(REPORT_DIR / 'confusion_matrix.png')
    
    # ROC Curve
    fpr, tpr, _ = roc_curve(y_test, probs)
    plt.figure()
    plt.plot(fpr, tpr, label=f'AUC = {roc_auc_score(y_test, probs):.2f}')
    plt.plot([0, 1], [0, 1], 'k--')
    plt.title('Curva ROC')
    plt.legend()
    plt.savefig(REPORT_DIR / 'roc_curve.png')
    
    print(f"   ✅ Gráficos guardados en: {REPORT_DIR}")

if __name__ == "__main__":
    run_final_pipeline()
