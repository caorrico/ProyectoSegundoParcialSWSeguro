import json
from abc import ABC, abstractmethod
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
from sklearn.model_selection import cross_val_score, train_test_split, RandomizedSearchCV

from app.domain.contracts import Dataset
from app.domain.entities import CodeModuleMetrics


class BaseTrainer(ABC):
    TARGET_COLUMN = "is_vulnerable"

    def __init__(self, model_path: Path, report_path: Path, random_state: int = 42, test_size: float = 0.25) -> None:
        self._model_path = model_path
        self._report_path = report_path
        self._random_state = random_state
        self._test_size = test_size

    @abstractmethod
    def _create_base_model(self) -> Any:
        """Create and return the underlying scikit-learn compatible classifier."""
        pass

    def _get_param_grid(self) -> Dict[str, Any]:
        """Return hyperparameter grid for tuning. Subclasses should override this if tuning is supported."""
        return {}

    def train(self, dataset: Dataset, tune: bool = False) -> Dict[str, object]:
        dataset_frame = pd.DataFrame(dataset)
        is_syntactic = "raw_code" in dataset_frame.columns
        
        if is_syntactic:
            self._validate_syntactic_dataset(dataset_frame)
            x = dataset_frame["raw_code"]
        else:
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

        base_estimator = self._create_base_model()
        
        if is_syntactic:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.pipeline import Pipeline, FeatureUnion
            from app.infrastructure.ml.ast_extractor import ASTFeatureExtractor
            model = Pipeline([
                ("features", FeatureUnion([
                    ("tfidf", TfidfVectorizer(max_features=1000)),
                    ("ast", ASTFeatureExtractor())
                ])),
                ("clf", base_estimator)
            ])
        else:
            model = base_estimator

        if tune:
            param_grid = self._get_param_grid()
            if param_grid:
                if is_syntactic:
                    param_grid = {f"clf__{k}": v for k, v in param_grid.items()}
                
                print(f"Starting Hyperparameter Tuning with {len(param_grid)} parameter spaces...")
                search = RandomizedSearchCV(
                    estimator=model,
                    param_distributions=param_grid,
                    n_iter=10,
                    scoring="f1",
                    cv=3,
                    n_jobs=-1,
                    random_state=self._random_state,
                    verbose=1
                )
                search.fit(x_train, y_train)
                print(f"Best parameters found: {search.best_params_}")
                model = search.best_estimator_
            else:
                print("No hyperparameter grid defined for this model. Skipping tuning.")
                model.fit(x_train, y_train)
        else:
            model.fit(x_train, y_train)

        predictions = model.predict(x_test)
        probabilities = model.predict_proba(x_test)[:, 1]

        clf_model = model.named_steps["clf"] if is_syntactic else model
        if is_syntactic:
            feature_names = model.named_steps["features"].get_feature_names_out().tolist()
        else:
            feature_names = CodeModuleMetrics.FEATURE_NAMES

        # Some models don't have feature_importances_ (like SVM with non-linear kernels)
        feature_importances = {}
        if hasattr(clf_model, "feature_importances_"):
            feature_importances = {
                feature: round(float(importance), 4)
                for feature, importance in zip(feature_names, clf_model.feature_importances_)
            }

        metrics = {
            "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
            "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
            "cross_validation_f1_mean": round(
                float(cross_val_score(model, x, y, cv=min(5, len(x)), scoring="f1").mean()) if len(x) >= 2 else 0.0, 4
            ),
            "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
            "feature_importances": feature_importances,
        }

        # Final fit on entire dataset
        model.fit(x, y)
        
        if self._model_path is not None:
            self._model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(model, self._model_path)
            if is_syntactic and hasattr(model, "named_steps"):
                joblib.dump(model.named_steps["features"], self._model_path.parent / "vectorizer.joblib")

        if self._report_path is not None:
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

    def _validate_syntactic_dataset(self, dataset: pd.DataFrame) -> None:
        required_columns = ["raw_code", self.TARGET_COLUMN]
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
