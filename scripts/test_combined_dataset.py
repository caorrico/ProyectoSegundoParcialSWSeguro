#!/usr/bin/env python3
"""
Prueba rápida para verificar cuántas muestras se cargan con el dataset combinado
"""
import sys
from pathlib import Path

# Add the project root directory to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.repositories.combined_dataset_repository import CombinedDatasetRepository

def main():
    print("=" * 60)
    print("PRUEBA: Cargando dataset combinado (TODOS los datos)")
    print("=" * 60)
    
    repo = CombinedDatasetRepository(limit_per_source=None)
    dataset = repo.load()
    
    print(f"\n✅ TOTAL de muestras cargadas: {len(dataset)}")
    
    # Contar cuántas son vulnerables vs seguras
    vulnerable = sum(1 for item in dataset if item["is_vulnerable"] == 1)
    safe = sum(1 for item in dataset if item["is_vulnerable"] == 0)
    
    print(f"   - Muestras vulnerables: {vulnerable} ({vulnerable/len(dataset)*100:.1f}%)")
    print(f"   - Muestras seguras: {safe} ({safe/len(dataset)*100:.1f}%)")
    
    print("\n✅ Dataset cargado correctamente!")
    print(f"   Ejemplo de muestra: {dataset[0] if dataset else 'Ninguna'}")
    print("=" * 60)

if __name__ == "__main__":
    main()
