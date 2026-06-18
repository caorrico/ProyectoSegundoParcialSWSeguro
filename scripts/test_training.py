#!/usr/bin/env python3
"""
Prueba de entrenamiento con un subconjunto pequeño
"""
import sys
from pathlib import Path

# Add the project root directory to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.domain.contracts import Dataset
from app.infrastructure.repositories.cvefixes_dataset_repository import CVEFixesDatasetRepository
from app.infrastructure.ml.random_forest_trainer import RandomForestTrainer
from app.shared.settings import Settings

def main():
    print("=" * 60)
    print("PRUEBA: Entrenamiento con 1000 muestras de CVEFixes")
    print("=" * 60)

    # Paso 1: Cargar un subconjunto pequeño de CVEFixes
    repo = CVEFixesDatasetRepository(Path("data/CVEFixes.csv/CVEFixes.csv"))
    full_dataset = repo.load()
    
    small_dataset = full_dataset[:1000]
    print(f"\n✅ Dataset pequeño cargado: {len(small_dataset)} muestras")
    
    # Paso 2: Configurar y ejecutar entrenamiento
    settings = Settings()
    trainer = RandomForestTrainer(
        model_path=settings.model_path,
        report_path=settings.metrics_report_path,
        random_state=settings.random_state,
        test_size=settings.test_size
    )
    
    print("\nIniciando entrenamiento...")
    metrics = trainer.train(small_dataset, tune=False)
    
    print("\n✅ Entrenamiento completado!")
    print(f"   Accuracy: {metrics['accuracy']:.4f}")
    print(f"   Precision: {metrics['precision']:.4f}")
    print(f"   Recall: {metrics['recall']:.4f}")
    print(f"   F1 Score: {metrics['f1_score']:.4f}")
    print(f"   ROC AUC: {metrics['roc_auc']:.4f}")
    
    print("\n✅ Modelo guardado en:", settings.model_path)
    print("✅ Reporte guardado en:", settings.metrics_report_path)
    print("=" * 60)
    
if __name__ == "__main__":
    main()
