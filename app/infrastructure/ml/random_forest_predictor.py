import re
from pathlib import Path
from typing import Tuple, Union

import joblib
import pandas as pd

from app.domain.entities import CodeModuleMetrics, RawCodeModule


def _detect_language_from_code(code: str) -> str:
    if re.search(r"\b(public\s+class|import\s+java|package\s+[\w.]+;)", code):
        return "java"
    if re.search(r"#include\s*<|std::|->", code):
        return "cpp"
    if re.search(r"<\?php|\bnamespace\s+[\w\\]+;", code):
        return "php"
    if re.search(r"\bdef\s+\w+\(|import\s+\w+", code):
        return "python"
    if re.search(r"\bfunction\s+\w+\(|const\s+\w+\s*=", code):
        return "javascript"
    if re.search(r"<!doctype html|<html", code, re.IGNORECASE):
        return "html"
    return "unknown"


def _raw_code_features(code: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "raw_code": code,
                "language": _detect_language_from_code(code),
                "source": "manual",
                "code_length": len(code),
                "line_count": len([line for line in code.splitlines() if line.strip()]),
            }
        ]
    )


def _predict_proba_raw_code(model, code: str) -> float:
    try:
        return float(model.predict_proba(_raw_code_features(code))[0][1])
    except Exception:
        return float(model.predict_proba(pd.Series([code]))[0][1])

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
            probability = _predict_proba_raw_code(model, metrics.raw_code)
            is_vulnerable = probability >= 0.50
            return is_vulnerable, probability

        else:
            features = pd.DataFrame([metrics.to_feature_dict()])[list(CodeModuleMetrics.FEATURE_NAMES)]
            
        probability = float(model.predict_proba(features)[0][1])
        is_vulnerable = probability >= 0.50
        return is_vulnerable, probability

    def get_top_features(self, metrics: Union[CodeModuleMetrics, RawCodeModule], top_n: int = 3) -> list[str]:
        import numpy as np

        if not self._model_path.exists():
            return []

        try:
            model = joblib.load(self._model_path)
            is_syntactic = isinstance(metrics, RawCodeModule)
            
            if is_syntactic:
                features_raw = _raw_code_features(metrics.raw_code)
                feature_union = model.named_steps["features"]
                rf = model.named_steps["clf"]
                try:
                    features_transformed = feature_union.transform(features_raw)
                except Exception:
                    features_raw = pd.Series([metrics.raw_code])
                    features_transformed = feature_union.transform(features_raw)
                feature_names = feature_union.get_feature_names_out()
                if hasattr(features_transformed, "toarray"):
                    features_transformed = features_transformed.toarray()
                features = pd.DataFrame(features_transformed, columns=feature_names)
                explainer_model = rf
            else:
                features = pd.DataFrame([metrics.to_feature_dict()])[list(CodeModuleMetrics.FEATURE_NAMES)]
                feature_names = list(CodeModuleMetrics.FEATURE_NAMES)
                explainer_model = model

            import shap
            # Mandatory SHAP with approximate=True for speed
            explainer = shap.TreeExplainer(explainer_model)
            shap_values = explainer.shap_values(features, approximate=True)

            if isinstance(shap_values, list):
                sv = shap_values[1][0]
            elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
                sv = shap_values[0, :, 1]
            else:
                sv = shap_values[0]

            # Get indices of top positive SHAP values
            top_indices = np.argsort(sv)[-top_n:][::-1]
            
            top_features_names = []
            for idx in top_indices:
                if sv[idx] > 0: # Only include features that positively contributed
                    name = feature_names[idx]
                    name = name.replace("tfidf__", "").replace("ast__ast_", "ast_")
                    top_features_names.append(name)
                    
            return top_features_names if top_features_names else ["No specific SHAP features isolated"]
        except Exception as e:
            print(f"Error in feature explainability: {e}")
            return ["Explainability unavailable"]

    def generate_explanation(self, metrics: Union[CodeModuleMetrics, RawCodeModule], report_path: Path) -> None:
        import shap
        import numpy as np

        if not self._model_path.exists():
            raise FileNotFoundError(f"Model not found at {self._model_path}.")

        model = joblib.load(self._model_path)
        is_syntactic = isinstance(metrics, RawCodeModule)
        
        if is_syntactic:
            features_raw = _raw_code_features(metrics.raw_code)
            feature_union = model.named_steps["features"]
            rf = model.named_steps["clf"]
            try:
                features_transformed = feature_union.transform(features_raw)
            except Exception:
                features_raw = pd.Series([metrics.raw_code])
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
