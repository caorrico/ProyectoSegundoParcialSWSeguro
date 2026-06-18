#!/usr/bin/env python3
"""
Prueba de tiempo de entrenamiento con 500 y 1000 muestras
y estimación para el dataset completo
"""
import sys
import time
from pathlib import Path

# Add the project root directory to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.domain.contracts import Dataset
from app.infrastructure.repositories.cvefixes_dataset_repository import CVEFixesDatasetRepository
from app.infrastructure.ml.random_forest_trainer import RandomForestTrainer
from app.shared.settings import Settings

def test_training(dataset: Dataset, n_samples: int, model_suffix: str):
    subset = dataset[:n_samples]
    print(f"\n--- ENTRENANDO CON {n_samples} MUESTRAS ---")
    settings = Settings()
    trainer = RandomForestTrainer(
        model_path=settings.model_path.parent / f"test_model_{model_suffix}.joblib",
        report_path=settings.metrics_report_path.parent / f"test_metrics_{model_suffix}.json",
        random_state=settings.random_state,
        test_size=settings.test_size
    )
    
    start_time = time.time()
    metrics = trainer.train(subset, tune=False)
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    print(f"   ⏱️ Tiempo total: {elapsed_time:.2f} segundos ({elapsed_time/60:.2f} minutos)")
    print(f"   📊 Accuracy: {metrics['accuracy']:.4f}")
    print(f"   📊 F1 Score: {metrics['f1_score']:.4f}")
    return elapsed_time

def main():
    print("=" * 70)
    print("PRUEBA DE TIEMPO DE ENTRENAMIENTO")
    print("=" * 70)
    
    # Paso 1: Cargar dataset completo
    repo = CVEFixesDatasetRepository(Path("data/CVEFixes.csv/CVEFixes.csv"))
    full_dataset = repo.load()
    print(f"\n✅ Dataset completo: {len(full_dataset)} muestras")
    
    # Paso 2: Probar con 500 y 1000 muestras
    time_500 = test_training(full_dataset, 500, "500")
    time_1000 = test_training(full_dataset, 1000, "1000")
    
    # Paso 3: Estimar tiempo para dataset completo (75,844 muestras)
    full_n = 75844
    # Estimación lineal: tiempo es proporcional al número de muestras
    # Usamos el tiempo de 1000 muestras para la estimación
    est_time_full_linear_1000 = (time_1000 / 1000) * full_n
    # También podemos usar el tiempo de 500 para comparar
    est_time_full_linear_500 = (time_500 / 500) * full_n
    
    print("\n" + "=" * 70)
    print("ESTIMACIÓN DE TIEMPO PARA DATASET COMPLETO")
    print("=" * 70)
    print(f"   Tamaño completo: {full_n} muestras")
    print(f"\n   Estimación (lineal, desde 500 muestras):")
    print(f"      ⏱️ {est_time_full_linear_500:.2f} segundos ({est_time_full_linear_500/60:.2f} minutos, {est_time_full_linear_500/3600:.2f} horas)")
    print(f"\n   Estimación (lineal, desde 1000 muestras):")
    print(f"      ⏱️ {est_time_full_linear_1000:.2f} segundos ({est_time_full_linear_1000/60:.2f} minutos, {est_time_full_linear_1000/3600:.2f} horas)")
    
    # Nota: El tiempo real puede ser menor, ya que la extracción de features es una parte
    # fija que no escala linealmente con el número de muestras
    print("\n💡 NOTA: La extracción de features (TF-IDF + AST) es una parte que no escala 100% linealmente,")
    print("   así que el tiempo real probablemente sea un poco menor que la estimación lineal!")
    print("=" * 70)

if __name__ == "__main__":
    main()
