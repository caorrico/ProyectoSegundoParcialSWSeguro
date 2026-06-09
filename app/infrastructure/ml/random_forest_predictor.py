from pathlib import Path
from typing import Tuple

import joblib
import pandas as pd

from app.domain.entities import CodeModuleMetrics


class RandomForestPredictor:
    def __init__(self, model_path: Path) -> None:
        self._model_path = model_path

    def predict(self, metrics: CodeModuleMetrics) -> Tuple[bool, float]:
        if not self._model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {self._model_path}. Run: python -m app.interfaces.cli train"
            )

        model = joblib.load(self._model_path)
        features = pd.DataFrame([metrics.to_feature_dict()])[list(CodeModuleMetrics.FEATURE_NAMES)]
        probability = float(model.predict_proba(features)[0][1])
        is_vulnerable = probability >= 0.70
        return is_vulnerable, probability
