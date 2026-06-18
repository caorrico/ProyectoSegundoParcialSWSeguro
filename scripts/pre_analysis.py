from pathlib import Path
import json
import re

# Asegurar path
PROJECT_ROOT = Path('.').resolve()
if PROJECT_ROOT.name == 'scripts':
    PROJECT_ROOT = PROJECT_ROOT.parent

def pre_analysis_check(code_path: Path):
    """
    Analisis estático rápido (heurístico) como etapa inicial del Pipeline CI/CD.
    """
    code = code_path.read_text(encoding='utf-8')
    
    # Reglas prohibidas de alto riesgo
    forbidden = [
        (r'\bgets\s*\(', "Uso de gets() inseguro"),
        (r'\bstrcpy\s*\(', "Uso de strcpy() inseguro"),
        (r'\bgets\s*\(', "Uso de gets() inseguro"),
        (r'\beval\s*\(', "Uso de eval() peligroso")
    ]
    
    issues = []
    for pattern, msg in forbidden:
        if re.search(pattern, code):
            issues.append(msg)
            
    if issues:
        print(f"⚠️ [PRE-ANÁLISIS] Problemas detectados en {code_path.name}: {issues}")
        return False
    print(f"✅ [PRE-ANÁLISIS] {code_path.name} limpio.")
    return True

if __name__ == "__main__":
    # Test rápido
    sample = PROJECT_ROOT / 'examples' / 'vulnerable_sample.cpp'
    if sample.exists():
        pre_analysis_check(sample)
