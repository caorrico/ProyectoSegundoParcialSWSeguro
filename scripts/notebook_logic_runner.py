#!/usr/bin/env python3
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Fix imports
PROJECT_ROOT = Path('.').resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.infrastructure.repositories.dataset_cleaning import build_clean_training_frame
from sklearn.model_selection import GroupShuffleSplit
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay

# Configuration
TEST_SIZE = 0.25
VALIDATION_SIZE = 0.20
SYNTHETIC_SOURCES = {'owasp2025'}
FEATURE_COLUMNS = ['raw_code', 'language', 'source', 'code_length', 'line_count']

def run_notebook_logic():
    print("--- 1. Limpieza ---")
    build_result = build_clean_training_frame(PROJECT_ROOT, include_cvefixes=True)
    df = build_result.frame.copy()
    
    print("--- 2. Split ---")
    real_df = df[~df['source'].isin(SYNTHETIC_SOURCES)].copy()
    df[df['source'].isin(SYNTHETIC_SOURCES)].copy()
    
    real_groups = real_df['group_id'].where(real_df['group_id'].astype(str).str.len() > 0, real_df['code_hash'])
    splitter = GroupShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=42)
    train_idx, test_idx = next(splitter.split(real_df, real_df['is_vulnerable'], groups=real_groups))
    
    train_real_df = real_df.iloc[train_idx].copy()
    test_df = real_df.iloc[test_idx].copy()
    
    val_groups = train_real_df['group_id'].where(train_real_df['group_id'].astype(str).str.len() > 0, train_real_df['code_hash'])
    val_splitter = GroupShuffleSplit(n_splits=1, test_size=VALIDATION_SIZE, random_state=42)
    fit_idx, valid_idx = next(val_splitter.split(train_real_df, train_real_df['is_vulnerable'], groups=val_groups))
    
    fit_df = train_real_df.iloc[fit_idx].copy()
    valid_df = train_real_df.iloc[valid_idx].copy()
    
    X_fit = fit_df[FEATURE_COLUMNS]
    y_fit = fit_df['is_vulnerable'].astype(int)
    valid_df[FEATURE_COLUMNS]
    valid_df['is_vulnerable'].astype(int)
    train_real_df[FEATURE_COLUMNS]
    train_real_df['is_vulnerable'].astype(int)
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df['is_vulnerable'].astype(int)

    print("--- 3. Pipeline ---")
    features = ColumnTransformer([
        ('word_hash', HashingVectorizer(n_features=2**14, alternate_sign=False), 'raw_code'),
        ('category', OneHotEncoder(handle_unknown='ignore'), ['language', 'source']),
        ('numeric', StandardScaler(with_mean=False), ['code_length', 'line_count']),
    ])
    pipeline = Pipeline([('features', features), ('clf', SGDClassifier(loss='log_loss', class_weight='balanced', random_state=42))])
    
    pipeline.fit(X_fit, y_fit)
    
    print("--- 4. Evaluación ---")
    probs = pipeline.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    
    print(classification_report(y_test, preds))
    
    # Save confusion matrix
    cm = confusion_matrix(y_test, preds)
    ConfusionMatrixDisplay(cm).plot()
    plt.savefig('reports/notebook_confusion_matrix.png')
    print("Gráficos guardados en reports/")

if __name__ == "__main__":
    run_notebook_logic()
