#!/usr/bin/env python3
"""
Experimento para predecir la curva de tiempo de entrenamiento.
Ejecuta benchmarks con tamaños crecientes y proyecta el tiempo total.
"""
import sys
import os
import json
import re
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.base import BaseEstimator, TransformerMixin
from scipy.sparse import csr_matrix

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# === EXTRACTORES (Versión optimizada para el benchmark) ===

class SecurityFeatureExtractor(BaseEstimator, TransformerMixin):
    DANGEROUS_FUNCTIONS = {
        'buffer_overflow': [r'\bstrcpy\s*\(', r'\bstrcat\s*\(', r'\bsprintf\s*\(', r'\bgets\s*\('],
        'injection': [r'\bexec\s*\(', r'\beval\s*\(', r'\bsystem\s*\(', r'SELECT.*FROM'],
    }
    def fit(self, X, y=None):
        return self
    def transform(self, X, y=None):
        features = []
        for code in X:
            if not isinstance(code, str): code = ''
            row = [sum(len(re.findall(p, code, re.IGNORECASE)) for p in pats) for pats in self.DANGEROUS_FUNCTIONS.values()]
            row.append(len(code))
            features.append(row)
        return csr_matrix(np.array(features, dtype=np.float64))
    def get_feature_names_out(self, input_features=None):
        return np.array([f'sec_{cat}' for cat in self.DANGEROUS_FUNCTIONS.keys()] + ['length'])

class RobustASTFeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self): self._parser = None
    def _init(self):
        if self._parser is None:
            try:
                import tree_sitter, tree_sitter_cpp
                lang = tree_sitter.Language(tree_sitter_cpp.language(), 'cpp')
                self._parser = tree_sitter.Parser()
                self._parser.set_language(lang)
            except: self._parser = 'off'
    def fit(self, X, y=None): return self
    def transform(self, X, y=None):
        self._init()
        features = []
        for code in X:
            if self._parser == 'off' or not isinstance(code, str): features.append([0])
            else:
                try:
                    tree = self._parser.parse(bytes(code, 'utf8'))
                    count = 0
                    stack = [tree.root_node]
                    while stack:
                        n = stack.pop()
                        count += 1
                        stack.extend(n.children)
                    features.append([count])
                except: features.append([0])
        return csr_matrix(np.array(features))
    def get_feature_names_out(self, input_features=None): return np.array(['ast_nodes'])

def load_jsonl(path, limit=None):
    data = []
    if not Path(path).exists(): return data
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if limit and i >= limit: break
            try:
                item = json.loads(line)
                code = item.get('func') or item.get('code') or item.get('functionSource') or ''
                label = item.get('target') or item.get('label') or 0
                if code: data.append({'raw_code': code, 'is_vulnerable': int(label)})
            except: continue
    return data

def run_benchmark(X, y, size):
    indices = np.random.choice(len(X), size, replace=False)
    X_sub, y_sub = X[indices], y[indices]
    
    pipeline = FeatureUnion([
        ('tfidf', TfidfVectorizer(max_features=1000)),
        ('ast', RobustASTFeatureExtractor()),
        ('sec', SecurityFeatureExtractor()),
    ])
    
    start_feat = time.time()
    X_feat = pipeline.fit_transform(X_sub)
    t_feat = time.time() - start_feat
    
    start_train = time.time()
    rf = RandomForestClassifier(n_estimators=100, n_jobs=-1)
    rf.fit(X_feat, y_sub)
    t_train = time.time() - start_train
    
    return t_feat, t_train

def main():
    print("📈 Iniciando experimento de escalabilidad temporal...")
    
    # Cargar datos base
    raw_data = load_jsonl(PROJECT_ROOT / 'data/codexglue/train.jsonl', limit=5000)
    if not raw_data:
        print("❌ No hay datos para el benchmark.")
        return
        
    df = pd.DataFrame(raw_data)
    X = np.array(df['raw_code'].tolist())
    y = np.array(df['is_vulnerable'].tolist())
    
    sizes = [200, 500, 1000, 2000]
    results = []
    
    for s in sizes:
        print(f"  Testing size: {s}...")
        tf, tt = run_benchmark(X, y, s)
        results.append({'size': s, 'feat_time': tf, 'train_time': tt, 'total': tf + tt})
        print(f"    -> Features: {tf:.2f}s, Train: {tt:.2f}s")
    
    df_res = pd.DataFrame(results)
    
    # Proyección lineal (Heurística simple: O(n log n) para train, O(n) para feat)
    # Usaremos una proyección lineal simple para dar una idea conservadora
    last_total = df_res.iloc[-1]['total']
    last_size = df_res.iloc[-1]['size']
    
    targets = [5000, 10000, 25000, 50000]
    
    print("\n" + "="*50)
    print("  PROYECCIÓN DE TIEMPO ESTIMADO")
    print("="*50)
    print(f"{'Muestras':<15} | {'Tiempo Est.':<15}")
    print("-" * 35)
    
    for t in targets:
        # Estimación: (tiempo_actual / tamaño_actual) * tamaño_objetivo
        # Para Random Forest el escalado suele ser algo peor que lineal, pero para Features es lineal.
        est_seconds = (last_total / last_size) * t
        
        # Ajuste no lineal para entrenamiento (log n factor)
        # Factor de penalización por tamaño para Random Forest
        if t > last_size:
            factor = np.log2(t) / np.log2(last_size)
            est_seconds *= factor
            
        est_minutes = est_seconds / 60
        if est_minutes > 60:
            print(f"{t:<15,} | {est_minutes/60:.2f} horas")
        else:
            print(f"{t:<15,} | {est_minutes:.2f} min")
    print("="*50)
    print("ponytail: estimación basada en regresión lineal simple + factor logarítmico para RF.")

if __name__ == "__main__":
    main()
