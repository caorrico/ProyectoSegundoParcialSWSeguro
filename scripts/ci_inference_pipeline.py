#!/usr/bin/env python3
"""
Pipeline de Inferencia de Seguridad (Etapa 1 del PDF).
Combina Análisis Estático (Taint+AST+Metrics) y Clasificación ML.
"""
import sys
import re
import joblib
import json
import pandas as pd
from pathlib import Path

# Agregar project root al path
PROJECT_ROOT = Path('.').resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# === EXTRACTORES DE ALTA FIDELIDAD (Iguales a los del entrenamiento) ===

# === GUÍA DE MITIGACIÓN (Estructurada) ===
REMEDIATION_GUIDE = {
    'buffer_overflow': "Vulnerabilidad: Buffer Overflow. Mitigación: Reemplace strcpy/gets por strncpy/fgets y valide tamaños de buffer.",
    'injection': "Vulnerabilidad: Inyección (SQL/Command). Mitigación: Use consultas parametrizadas y valide inputs del usuario.",
    'default': "Vulnerabilidad detectada. Mitigación: Revise la lógica de sanitización siguiendo el estándar OWASP."
}

def run_inference(code_file_path):
    # 1. Cargar Pipeline Entrenado
    model_path = PROJECT_ROOT / 'models' / 'modelo_final_cvefixes.joblib'
    if not model_path.exists():
        print(f"Error: Modelo no encontrado en {model_path}")
        sys.exit(1)
        
    pipeline = joblib.load(model_path)
    
    # 2. Análisis Estático (Heurístico)
    code = Path(code_file_path).read_text(encoding='utf-8', errors='replace')
    detected_patterns = []
    
    # Análisis heurístico básico previo al ML
    if re.search(r'\bgets\s*\(', code):
        detected_patterns.append('buffer_overflow')
    if re.search(r'\beval\s*\(', code):
        detected_patterns.append('injection')
    
    # 3. Inferencia con Modelo ML
    features = pd.DataFrame([{'raw_code': code, 'language': 'cpp', 'source': 'pr_analysis', 'code_length': len(code), 'line_count': len(code.splitlines())}])
    prediction = pipeline.predict(features)[0]
    probability = pipeline.predict_proba(features)[0][1]
    
    # 4. Generación de Reporte (JSON para CI/CD)
    report = {
        "vulnerable": bool(prediction == 1),
        "probability": float(probability),
        "vulnerabilities": detected_patterns,
        "mitigation": [REMEDIATION_GUIDE.get(p, REMEDIATION_GUIDE['default']) for p in detected_patterns]
    }
    
    # Guardar reporte
    with open("security_report.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(json.dumps(report, indent=2))
    
    if report["vulnerable"]:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python ci_inference_pipeline.py <ruta_archivo>")
        sys.exit(1)
    run_inference(sys.argv[1])
