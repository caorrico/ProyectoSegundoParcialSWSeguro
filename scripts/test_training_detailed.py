#!/usr/bin/env python3
"""
Prueba de tiempo de entrenamiento con 500 y 1000 muestras,
separando tiempo de extracción de features vs entrenamiento del modelo
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
from app.infrastructure.ml.ast_extractor import ASTFeatureExtractor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.ensemble import RandomForestClassifier
from app.shared.settings import Settings

def test_feature_extraction(dataset: Dataset, n_samples: int):
    subset = dataset[:n_samples]
    codes = [item["raw_code"] for item in subset]
    print(f"\n--- EXTRAYENDO FEATURES DE {n_samples} MUESTRAS ---")
    
    start_time = time.time()
    
    # Misma pipeline de features que en BaseTrainer
    features = FeatureUnion([
        ("tfidf", TfidfVectorizer(max_features=1000)),
        ("ast", ASTFeatureExtractor())
    ])
    features.fit(codes)
    X = features.transform(codes)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"   ⏱️ Tiempo extracción: {elapsed_time:.2f} segundos ({elapsed_time/60:.2f} minutos)")
    print(f"   📊 Tamaño de features: {X.shape}")
    
    return elapsed_time, X

def test_model_training(X, y, n_samples: int):
    print(f"\n--- ENTRENANDO MODELO CON {n_samples} MUESTRAS ---")
    
    start_time = time.time()
    
    model = RandomForestClassifier(
        n_estimators=180,
        max_depth=10,
        class_weight="balanced",
        random_state=42
    )
    model.fit(X, y)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"   ⏱️ Tiempo entrenamiento: {elapsed_time:.2f} segundos ({elapsed_time/60:.2f} minutos)")
    
    return elapsed_time

def main():
    print("=" * 70)
    print("PRUEBA DE TIEMPO DETALLADA")
    print("=" * 70)
    
    # Paso 1: Cargar dataset
    repo = CVEFixesDatasetRepository(Path("data/CVEFixes.csv/CVEFixes.csv"))
    full_dataset = repo.load()
    print(f"\n✅ Dataset completo: {len(full_dataset)} muestras")
    
    # Paso 2: Pruebas con 500 muestras
    time_feat_500, X_500 = test_feature_extraction(full_dataset, 500)
    y_500 = [item["is_vulnerable"] for item in full_dataset[:500]]
    time_train_500 = test_model_training(X_500, y_500, 500)
    total_500 = time_feat_500 + time_train_500
    print(f"   TOTAL 500 muestras: {total_500:.2f}s ({total_500/60:.2f}min)")
    
    # Paso 3: Pruebas con 1000 muestras
    time_feat_1000, X_1000 = test_feature_extraction(full_dataset, 1000)
    y_1000 = [item["is_vulnerable"] for item in full_dataset[:1000]]
    time_train_1000 = test_model_training(X_1000, y_1000, 1000)
    total_1000 = time_feat_1000 + time_train_1000
    print(f"   TOTAL 1000 muestras: {total_1000:.2f}s ({total_1000/60:.2f}min)")
    
    # Paso 4: Estimar para 75,844 muestras
    full_n = 75844
    # 1. Estimar tiempo extracción de features (suele escalar logarítmicamente o linealmente)
    # Asumimos que es lineal (peor caso)
    est_time_feat = (time_feat_1000 / 1000) * full_n
    # 2. Estimar tiempo entrenamiento (este sí escala más o menos linealmente con n_estimators y n_samples)
    est_time_train = (time_train_1000 / 1000) * full_n
    # Tiempo total
    est_time_total = est_time_feat + est_time_train
    
    print("\n" + "=" * 70)
    print("ESTIMACIÓN PRECISA PARA DATASET COMPLETO")
    print("=" * 70)
    print(f"   Tamaño completo: {full_n} muestras")
    print(f"\n   Desglose:")
    print(f"      🔍 Extracción de features: {est_time_feat:.2f}s ({est_time_feat/60:.2f}min, {est_time_feat/3600:.2f}h)")
    print(f"      🤖 Entrenamiento del modelo: {est_time_train:.2f}s ({est_time_train/60:.2f}min, {est_time_train/3600:.2f}h)")
    print(f"\n   TOTAL ESTIMADO: {est_time_total:.2f} segundos ({est_time_total/60:.2f} minutos, {est_time_total/3600:.2f} horas)")
    
    # Ajuste realista: la extracción de features suele escalar menos que linealmente
    est_time_feat_realistic = (time_feat_1000 / 1000**0.8) * full_n**0.8
    est_time_total_realistic = est_time_feat_realistic + est_time_train
    print(f"\n💡 Estimación más REALISTA (asumiendo extracción con 0.8): {est_time_total_realistic/60:.2f} minutos ({est_time_total_realistic/3600:.2f} horas)")
    print("=" * 70)

if __name__ == "__main__":
    main()
