import json
from pathlib import Path
from typing import Dict, Any

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from app.infrastructure.ml.base_trainer import BaseTrainer
from app.infrastructure.ml.vulberta_wrapper import VulBERTaWrapper
from app.domain.contracts import Dataset


class VulBERTaTrainer(BaseTrainer):
    """
    Trainer for the VulBERTa Deep Learning model.
    
    Unlike traditional ML trainers, this one:
    - Skips cross-validation (the model is pre-trained, no need to re-fit 5 times)
    - Skips FeatureUnion/TF-IDF pipeline (VulBERTa has its own internal tokenizer)
    - Feeds raw source code directly to the Hugging Face pipeline
    """

    def __init__(self, model_path, report_path, random_state=42, test_size=0.25):
        super().__init__(model_path, report_path, random_state, test_size)

    def _create_base_model(self):
        return VulBERTaWrapper()

    def _get_param_grid(self):
        return {}

    def train(self, dataset: Dataset, tune: bool = False) -> Dict[str, object]:
        """
        Custom train method for VulBERTa that avoids cross-validation
        and the TF-IDF/AST pipeline. The model receives raw code directly.
        """
        dataset_frame = pd.DataFrame(dataset)

        if "raw_code" not in dataset_frame.columns:
            raise ValueError(
                "VulBERTa es un modelo de Deep Learning que analiza texto directamente. "
                "Necesita un dataset con código fuente real ('raw_code'). "
                "Por favor, añade un flag como --use-combined, --use-reveal o --use-vulberta."
            )

        self._validate_syntactic_dataset(dataset_frame)

        x = dataset_frame["raw_code"].tolist()
        y = dataset_frame[self.TARGET_COLUMN].tolist()

        x_train, x_test, y_train, y_test = train_test_split(
            x, y,
            test_size=self._test_size,
            random_state=self._random_state,
            stratify=y,
        )

        # Initialize the pre-trained model (downloads weights once from HuggingFace)
        model = self._create_base_model()
        model.fit(x_train, y_train)

        # Predict on test set
        print(f"Running VulBERTa predictions on {len(x_test)} test samples (this may take a few minutes on CPU)...")
        predictions = model.predict(x_test)
        probabilities = model.predict_proba(x_test)[:, 1]

        metrics = {
            "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
            "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
            "cross_validation_f1_mean": "N/A (pre-trained model)",
            "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
            "feature_importances": {},
        }

        # Save model
        if self._model_path is not None:
            self._model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(model, self._model_path)
            print(f"Model saved to {self._model_path}")

        # Save metrics report
        if self._report_path is not None:
            self._report_path.parent.mkdir(parents=True, exist_ok=True)
            self._report_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
            print(f"Metrics report saved to {self._report_path}")

        return metrics
