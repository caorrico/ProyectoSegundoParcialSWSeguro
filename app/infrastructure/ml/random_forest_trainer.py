import json
from pathlib import Path
from typing import Dict

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_score, train_test_split

from app.domain.contracts import Dataset
from app.domain.entities import CodeModuleMetrics


class RandomForestTrainer:
    TARGET_COLUMN = "is_vulnerable"

    def __init__(self, model_path: Path, report_path: Path, random_state: int = 42, test_size: float = 0.25) -> None:
        self._model_path = model_path
        self._report_path = report_path
        self._random_state = random_state
        self._test_size = test_size

    def train(self, dataset: Dataset) -> Dict[str, object]:
        dataset_frame = pd.DataFrame(dataset)
        self._validate_dataset(dataset_frame)
        x = dataset_frame[list(CodeModuleMetrics.FEATURE_NAMES)]
        y = dataset_frame[self.TARGET_COLUMN]

        x_train, x_test, y_train, y_test = train_test_split(
            x,
            y,
            test_size=self._test_size,
            random_state=self._random_state,
            stratify=y,
        )

        model = RandomForestClassifier(
            n_estimators=180,
            max_depth=10,
            class_weight="balanced",
            random_state=self._random_state,
        )
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        probabilities = model.predict_proba(x_test)[:, 1]

        metrics = {
            "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
            "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
            "cross_validation_f1_mean": round(
                float(cross_val_score(model, x, y, cv=5, scoring="f1").mean()), 4
            ),
            "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
            "feature_importances": {
                feature: round(float(importance), 4)
                for feature, importance in zip(CodeModuleMetrics.FEATURE_NAMES, model.feature_importances_)
            },
        }

        model.fit(x, y)
        self._model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, self._model_path)

        self._report_path.parent.mkdir(parents=True, exist_ok=True)
        self._report_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        return metrics

    def _validate_dataset(self, dataset: pd.DataFrame) -> None:
        required_columns = [*CodeModuleMetrics.FEATURE_NAMES, self.TARGET_COLUMN]
        missing_columns = [column for column in required_columns if column not in dataset.columns]
        if missing_columns:
            raise ValueError(f"Dataset is missing required columns: {missing_columns}")
        if dataset.empty:
            raise ValueError("Dataset cannot be empty.")
        if dataset[required_columns].isnull().any().any():
            raise ValueError("Dataset cannot contain missing values.")
        if not set(dataset[self.TARGET_COLUMN].unique()).issubset({0, 1}):
            raise ValueError("is_vulnerable must contain only 0 or 1.")
        if dataset[self.TARGET_COLUMN].nunique() < 2:
            raise ValueError("Dataset must contain both target classes.")
