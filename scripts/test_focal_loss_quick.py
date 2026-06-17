#!/usr/bin/env python3
"""
Prueba rápida del algoritmo Focal Loss (de teoria.md) con pocas muestras del dataset combinado.
Usa el HuggingFaceTrainer que implementa BinaryFocalLoss con alpha=0.85, gamma=2.0
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.infrastructure.repositories.combined_dataset_repository import CombinedDatasetRepository
from app.infrastructure.ml.huggingface_trainer import HuggingFaceTrainer
from app.shared.settings import settings

def main():
    print("=" * 70)
    print("  PRUEBA RÁPIDA: Focal Loss (teoria.md) con dataset combinado")
    print("  Usando pocas muestras para resultados rápidos")
    print("=" * 70)

    # Paso 1: Cargar dataset combinado con límite pequeño
    print("\n1. Cargando dataset combinado (limit_per_source=50)...")
    repo = CombinedDatasetRepository(limit_per_source=50)
    dataset = repo.load()
    print(f"    ✓ Total de muestras: {len(dataset):,}")
    
    # Contar clases
    vuln_count = sum(1 for d in dataset if d["is_vulnerable"])
    safe_count = len(dataset) - vuln_count
    print(f"    ✓ Muestras vulnerables: {vuln_count:,}")
    print(f"    ✓ Muestras seguras: {safe_count:,}")
    if safe_count > 0:
        print(f"    ✓ Ratio: {vuln_count / safe_count:.2f} vulnerables por seguro")

    # Paso 2: Configurar HuggingFaceTrainer con Focal Loss (algoritmo de teoria.md)
    print("\n2. Configurando HuggingFaceTrainer con Focal Loss...")
    print("    - alpha_loss=0.85 (peso clase vulnerable)")
    print("    - gamma_loss=2.0 (factor de enfoque)")
    print("    - epochs=1 (entrenamiento rápido)")
    print("    - batch_size=4 (memoria baja)")
    print("    - model=microsoft/codebert-base")
    
    trainer = HuggingFaceTrainer(
        model_path=Path("models/vuln_detector_test"),
        report_path=Path("reports/test_focal_loss_metrics.json"),
        model_name="microsoft/codebert-base",
        epochs=1,
        batch_size=4,
        alpha_loss=0.85,
        gamma_loss=2.0
    )

    # Paso 3: Entrenar
    print("\n3. Entrenando con Focal Loss (1 epoch)...")
    print("    (Esto puede tomar 1-2 minutos en CPU)")
    metrics = trainer.train(dataset)

    print("\n" + "=" * 70)
    print("  RESULTADOS - Focal Loss (teoria.md)")
    print("=" * 70)
    print(f"  Accuracy:  {metrics.get('accuracy', 0):.4f}")
    print(f"  Precision: {metrics.get('precision', 0):.4f}")
    print(f"  Recall:    {metrics.get('recall', 0):.4f}")
    print(f"  F1 Score:  {metrics.get('f1_score', 0):.4f}")
    print(f"  ROC AUC:   {metrics.get('roc_auc', 0):.4f}")
    print("=" * 70)
    
    print(f"\n✓ Modelo guardado en: models/vuln_detector_test")
    print(f"✓ Métricas guardadas en: reports/test_focal_loss_metrics.json")
    print("\n✅ Prueba completada exitosamente!")

if __name__ == "__main__":
    main()