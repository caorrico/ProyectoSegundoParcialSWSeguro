#!/usr/bin/env python3
"""
Pipeline de Inferencia para CI/CD (Etapa 1 del PDF).
Carga el modelo entrenado y evalúa código nuevo en Pull Requests.
"""
import sys
import re
import joblib
import pandas as pd
from pathlib import Path
from sklearn.base import BaseEstimator, TransformerMixin
from scipy.sparse import csr_matrix

# Agregar project root
PROJECT_ROOT = Path('.').resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# --- Extractores (Deben ser idénticos a los del entrenamiento) ---
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

# --- Script de Inferencia ---
def run_inference(code_file_path):
    model_path = PROJECT_ROOT / 'models' / 'modelo_final_cvefixes.joblib'
    if not model_path.exists():
        print(f"Error: Modelo no encontrado en {model_path}")
        sys.exit(1)
        
    pipeline = joblib.load(model_path)
    
    code = Path(code_file_path).read_text(encoding='utf-8')
    
    # Pre-análisis estático heurístico (Etapa 1: Revisión inicial)
    if re.search(r'\bgets\s*\(', code):
        print("VULNERABLE: Uso de gets() detectado")
        sys.exit(1)
        
    # Inferencia con el modelo ML
    features = pd.DataFrame([{'raw_code': code, 'language': 'cpp', 'source': 'pr_diff', 'code_length': len(code), 'line_count': len(code.splitlines())}])
    prediction = pipeline.predict(features)[0]
    probability = pipeline.predict_proba(features)[0][1]
    
    if prediction == 1:
        print(f"VULNERABLE detectado con probabilidad: {probability:.2%}")
        sys.exit(1)
    else:
        print("SEGURO")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python ci_inference_pipeline.py <ruta_archivo>")
        sys.exit(1)
    run_inference(sys.argv[1])
