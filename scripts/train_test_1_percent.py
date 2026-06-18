#!/usr/bin/env python3
"""Entrena y prueba el modelo con el 10% del dataset combinado para mejor entrenamiento."""
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import random
from app.infrastructure.repositories.combined_dataset_repository import CombinedDatasetRepository
from app.infrastructure.ml.random_forest_trainer import RandomForestTrainer
from app.shared.settings import settings


def main():
    print("=" * 70)
    print("  ENTRENAMIENTO Y PRUEBA CON 10% DEL DATASET COMBINADO (MEJORADO)")
    print("=" * 70)

    # Paso 1: Cargar el dataset combinado completo
    print("\n1. Cargando dataset combinado completo...")
    full_repo = CombinedDatasetRepository(limit_per_source=None)
    full_dataset = full_repo.load()
    print(f"    ✓ Total de muestras: {len(full_dataset):,}")

    # Paso 2: Tomar el 10% de las muestras (aleatorio)
    print("\n2. Seleccionando el 10% de las muestras (aleatorio)...")
    random.seed(settings.random_state)
    random.shuffle(full_dataset)
    dataset_size = int(len(full_dataset) * 0.10)
    selected_dataset = full_dataset[:dataset_size]
    print(f"    ✓ Muestras seleccionadas: {len(selected_dataset):,}")
    
    # Contar clases
    vuln_count = sum(1 for d in selected_dataset if d["is_vulnerable"])
    safe_count = len(selected_dataset) - vuln_count
    print(f"    ✓ Muestras vulnerables: {vuln_count:,}")
    print(f"    ✓ Muestras seguras: {safe_count:,}")
    print(f"    ✓ Ratio: {vuln_count / safe_count:.2f} vulnerables por seguro")

    # Paso 3: Crear un repositorio temporal
    print("\n3. Configurando entrenamiento...")
    class TempDatasetRepository:
        def __init__(self, data):
            self._data = data
        def load(self):
            return self._data

    trainer = RandomForestTrainer(
        model_path=settings.model_path,
        report_path=settings.metrics_report_path,
        random_state=settings.random_state,
        test_size=settings.test_size,
    )

    # Paso 4: Entrenar el modelo
    print("\n4. Entrenando el modelo MEJORADO...")
    from app.application.use_cases.train_vulnerability_model import TrainVulnerabilityModelUseCase
    use_case = TrainVulnerabilityModelUseCase(TempDatasetRepository(selected_dataset), trainer)
    metrics = use_case.execute(tune=False)

    print("\n" + "=" * 70)
    print("  MÉTRICAS DEL MODELO")
    print("=" * 70)
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall: {metrics['recall']:.4f}")
    print(f"  F1 Score: {metrics['f1_score']:.4f}")
    print(f"  ROC AUC: {metrics['roc_auc']:.4f}")
    print("\n  Confusion Matrix:")
    cm = metrics["confusion_matrix"]
    print(f"    [[TN: {cm[0][0]}, FP: {cm[0][1]}]")
    print(f"     [FN: {cm[1][0]}, TP: {cm[1][1]}]]")
    print(f"  True Negatives:  {cm[0][0]}")
    print(f"  False Positives: {cm[0][1]}")
    print(f"  False Negatives: {cm[1][0]}")
    print(f"  True Positives:  {cm[1][1]}")
    print("=" * 70)
    
    # Show top features
    if "feature_importances" in metrics:
        print("\n  TOP 10 FEATURE IMPORTANCES:")
        sorted_features = sorted(
            metrics["feature_importances"].items(),
            key=lambda x: x[1], reverse=True
        )[:10]
        for i, (feature, importance) in enumerate(sorted_features, 1):
            print(f"    {i}. {feature}: {importance:.4f}")

    print(f"\n✓ Modelo entrenado y guardado en: {settings.model_path}")
    print(f"✓ Reporte de métricas guardado en: {settings.metrics_report_path}")


if __name__ == "__main__":
    main()
