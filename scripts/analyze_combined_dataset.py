#!/usr/bin/env python3
"""Analiza el dataset combinado para verificar su calidad y diversidad."""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.repositories.combined_dataset_repository import CombinedDatasetRepository
from collections import Counter
import random


def main():
    print("=" * 80)
    print("  ANÁLISIS DEL DATASET COMBINADO")
    print("=" * 80)

    print("\n1. Cargando dataset combinado...")
    repo = CombinedDatasetRepository(limit_per_source=200)  # Limitamos para analizar rápido
    dataset = repo.load()
    print(f"   ✓ Total: {len(dataset)} muestras")

    # 2. Analizar campos por muestra
    print("\n2. Analizando campos por muestra...")
    field_counts = Counter()
    has_language_count = 0
    languages = []
    for sample in dataset:
        for k in sample.keys():
            field_counts[k] += 1
        if "language" in sample:
            has_language_count +=1
            languages.append(sample.get("language", "unknown"))

    print(f"   - Campos encontrados: {field_counts}")
    print(f"   - Muestras con campo 'language': {has_language_count}")
    if languages:
        print(f"   - Idiomas presentes: {Counter(languages)}")

    # 3. Analizar longitudes de código
    print("\n3. Analizando longitudes de código...")
    lengths = []
    for sample in dataset:
        code = sample.get("raw_code", "")
        lengths.append(len(code))

    import numpy as np
    print(f"   - Mín: {np.min(lengths)}, Med: {np.median(lengths):.0f}, Máx: {np.max(lengths)}, Media: {np.mean(lengths):.1f}")
    print(f"   - Percentiles: 25%={np.percentile(lengths, 25):.0f}, 75%={np.percentile(lengths, 75):.0f}")

    # 4. Distribución de etiquetas
    print("\n4. Distribución de etiquetas is_vulnerable...")
    labels = [1 if s.get("is_vulnerable", 0) else 0 for s in dataset]
    label_counter = Counter(labels)
    total = len(labels)
    print(f"   - Seguros (0): {label_counter.get(0, 0)} ({label_counter.get(0, 0)/total*100:.1f}%)")
    print(f"   - Vulnerables (1): {label_counter.get(1, 0)} ({label_counter.get(1, 0)/total*100:.1f}%)")

    # 5. Revisar algunas muestras aleatorias
    print("\n5. Revisando 3 muestras aleatorias...")
    random.seed(42)
    random_samples = random.sample(dataset, 3)
    for i, s in enumerate(random_samples, 1):
        print(f"\n--- Muestra {i} ---")
        print(f"is_vulnerable: {s.get('is_vulnerable')}")
        if "language" in s:
            print(f"language: {s.get('language')}")
        code = s.get("raw_code", "")
        print(f"raw_code (primeros 300 chars): {code[:300]}...")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
