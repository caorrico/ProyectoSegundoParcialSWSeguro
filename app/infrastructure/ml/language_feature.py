"""Language feature transformer."""
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from app.infrastructure.ml.language_detector import LanguageDetector

class LanguageFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract programming language as a feature."""

    def __init__(self):
        self.language_detector = LanguageDetector()

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        # X is a pandas Series or list of strings
        features = []
        for code in X:
            lang = self.language_detector.detect(str(code))
            # One-hot encoding for our target languages (others go to "other")
            features.append({
                "lang_c": 1 if lang == "c" else 0,
                "lang_cpp": 1 if lang == "cpp" else 0,
                "lang_java": 1 if lang == "java" else 0,
                "lang_python": 1 if lang == "python" else 0,
                "lang_javascript": 1 if lang == "javascript" else 0,
                "lang_php": 1 if lang == "php" else 0,
                "lang_ruby": 1 if lang == "ruby" else 0,
                "lang_go": 1 if lang == "go" else 0,
                "lang_other": 1 if lang in ["unknown", "other"] else 0,
            })
        
        # Convert to numpy array
        return np.array([
            [
                f["lang_c"], f["lang_cpp"], f["lang_java"], f["lang_python"],
                f["lang_javascript"], f["lang_php"], f["lang_ruby"],
                f["lang_go"], f["lang_other"]
            ] for f in features
        ])

    def get_feature_names_out(self, input_features=None):
        return np.array([
            "lang_c", "lang_cpp", "lang_java", "lang_python",
            "lang_javascript", "lang_php", "lang_ruby",
            "lang_go", "lang_other"
        ])
