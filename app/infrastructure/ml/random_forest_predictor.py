from pathlib import Path
from typing import Tuple

import joblib
import pandas as pd

from app.domain.entities import CodeModuleMetrics, RawCodeModule
from typing import Union

class RandomForestPredictor:
    def __init__(self, model_path: Path) -> None:
        self._model_path = model_path

    def predict(self, metrics: Union[CodeModuleMetrics, RawCodeModule]) -> Tuple[bool, float]:
        if not self._model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {self._model_path}. Run: python -m app.interfaces.cli train"
            )

        model = joblib.load(self._model_path)
        
        if isinstance(metrics, RawCodeModule):
            features = pd.Series([metrics.raw_code])
        else:
            features = pd.DataFrame([metrics.to_feature_dict()])[list(CodeModuleMetrics.FEATURE_NAMES)]
            
        probability = float(model.predict_proba(features)[0][1])
        is_vulnerable = probability >= 0.70
        return is_vulnerable, probability

    def generate_explanation(self, metrics: Union[CodeModuleMetrics, RawCodeModule], report_path: Path) -> None:
        import shap
        import numpy as np
        from sklearn.pipeline import Pipeline

        if not self._model_path.exists():
            raise FileNotFoundError(f"Model not found at {self._model_path}.")

        model = joblib.load(self._model_path)
        is_syntactic = isinstance(metrics, RawCodeModule)
        
        if is_syntactic:
            features_raw = pd.Series([metrics.raw_code])
            feature_union = model.named_steps["features"]
            rf = model.named_steps["rf"]
            features_transformed = feature_union.transform(features_raw)
            feature_names = feature_union.get_feature_names_out()
            if hasattr(features_transformed, "toarray"):
                features_transformed = features_transformed.toarray()
            features = pd.DataFrame(features_transformed, columns=feature_names)
            explainer_model = rf
        else:
            features = pd.DataFrame([metrics.to_feature_dict()])[list(CodeModuleMetrics.FEATURE_NAMES)]
            explainer_model = model

        explainer = shap.TreeExplainer(explainer_model)
        shap_values = explainer.shap_values(features)

        # Handle different SHAP versions output formats for Random Forest
        if isinstance(shap_values, list):
            sv = shap_values[1][0]
            ev = explainer.expected_value[1]
        elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
            sv = shap_values[0, :, 1]
            ev = explainer.expected_value[1]
        else:
            sv = shap_values[0]
            ev = explainer.expected_value if not isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value[1]

        html_plot = shap.force_plot(ev, sv, features.iloc[0], matplotlib=False)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        shap.save_html(str(report_path), html_plot)
