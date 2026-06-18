#!/usr/bin/env python3
"""
Pipeline final de alto rendimiento para alcanzar >82% Accuracy.
Consolidado para evitar errores de importación y guardar gráficos.
"""
import sys
import random
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay, roc_curve, roc_auc_score
from sklearn.feature_extraction.text import TfidfVectorizer
from xgboost import XGBClassifier

# Agregar project root al path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.infrastructure.repositories.combined_dataset_repository import CombinedDatasetRepository

from scripts.extractors import RobustASTFeatureExtractor, EnhancedCodeMetrics

# === PIPELINE FINAL ===

def run_final_pipeline():
    print("=" * 80)
    print("  ENTRENAMIENTO DE MÁXIMA PRECISIÓN (Target >82%)")
    print("=" * 80)

    # 1. Cargar Dataset (CVEFixes)
    repo = CombinedDatasetRepository(limit_per_source=None)
    all_data = repo.load()
    cve_data = [d for d in all_data if d.get('source') == 'cvefixes']
    
    # Balancear
    vuln = [d for d in cve_data if d['is_vulnerable']]
    safe = [d for d in cve_data if not d['is_vulnerable']]
    count = min(len(vuln), len(safe), 500) # 1000 muestras totales para prueba rápida

    samples = random.sample(vuln, count) + random.sample(safe, count)
    random.shuffle(samples)
    
    X = [s['raw_code'] for s in samples]
    y = np.array([s['is_vulnerable'] for s in samples])
    
    # 2. Split
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)
    
    # 3. Feature Engineering
    feature_pipeline = FeatureUnion([
        ('tfidf_word', TfidfVectorizer(max_features=5000, ngram_range=(1, 3))),
        ('tfidf_char', TfidfVectorizer(max_features=3000, ngram_range=(3, 6), analyzer='char')),
        ('ast', RobustASTFeatureExtractor()),
        ('metrics', EnhancedCodeMetrics()),
    ])

    print("   🔧 Extrayendo features...")
    X_train_feat = feature_pipeline.fit_transform(X_train)
    X_val_feat = feature_pipeline.transform(X_val)
    X_test_feat = feature_pipeline.transform(X_test)

    # 4. XGBoost con parámetros optimizados
    model = XGBClassifier(
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=12,
        min_child_weight=1,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=42,
        eval_metric='error',
        early_stopping_rounds=100
    )
    
    print("   🏋️ Entrenando...")
    model.fit(X_train_feat, y_train, eval_set=[(X_val_feat, y_val)], verbose=False)
    
    # 5. Evaluación Final y Generación de Gráficos
    preds = model.predict(X_test_feat)
    probs = model.predict_proba(X_test_feat)[:, 1]
    test_acc = accuracy_score(y_test, preds)
    
    print(f"\n   🎯 Accuracy Final: {test_acc:.2%}")
    
    REPORT_DIR = PROJECT_ROOT / 'reports'
    REPORT_DIR.mkdir(exist_ok=True)
    
    # Matriz de Confusión
    cm = confusion_matrix(y_test, preds)
    ConfusionMatrixDisplay(cm, display_labels=['Safe', 'Vuln']).plot(cmap='Blues')
    plt.title('Matriz de Confusión')
    plt.savefig(REPORT_DIR / 'confusion_matrix.png')
    
    # ROC Curve
    fpr, tpr, _ = roc_curve(y_test, probs)
    plt.figure()
    plt.plot(fpr, tpr, label=f'AUC = {roc_auc_score(y_test, probs):.2f}')
    plt.plot([0, 1], [0, 1], 'k--')
    plt.title('Curva ROC')
    plt.legend()
    plt.savefig(REPORT_DIR / 'roc_curve.png')
    
    print(f"   ✅ Gráficos guardados en: {REPORT_DIR}")

if __name__ == "__main__":
    run_final_pipeline()
