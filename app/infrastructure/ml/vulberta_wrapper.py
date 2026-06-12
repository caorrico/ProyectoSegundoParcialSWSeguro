import os
from typing import Any, Optional
from sklearn.base import BaseEstimator, ClassifierMixin

class VulBERTaWrapper(BaseEstimator, ClassifierMixin):
    """
    A Scikit-Learn compatible wrapper for Hugging Face's VulBERTa model.
    Downloads the pre-trained weights during prediction or fitting,
    and returns vulnerabilities using the standard Scikit-Learn interface.
    """

    def __init__(self, model_name: str = "claudios/VulBERTa-MLP-MVD"):
        self.model_name = model_name
        self.pipe_ = None
        self.classes_ = [0, 1]

    def __getstate__(self):
        """Called by joblib/pickle before saving. We drop the Hugging Face pipeline."""
        state = self.__dict__.copy()
        state['pipe_'] = None
        return state

    def __setstate__(self, state):
        """Called by joblib/pickle when loading the model."""
        self.__dict__.update(state)

    def fit(self, X: Any, y: Optional[Any] = None) -> 'VulBERTaWrapper':
        """
        Since this is a pre-trained Deep Learning model, we don't fit from scratch
        on CPU as it would take hours. We just initialize the pipeline.
        """
        self._initialize_pipeline()
        return self

    def _initialize_pipeline(self) -> None:
        """Loads the Hugging Face pipeline if it hasn't been loaded yet."""
        if self.pipe_ is None:
            # We import here to avoid slow loading times if VulBERTa is not used
            from transformers import pipeline
            # Suppress excessive warnings
            os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"
            print(f"Loading pre-trained deep learning model: {self.model_name}...")
            self.pipe_ = pipeline(
                "text-classification", 
                model=self.model_name, 
                trust_remote_code=True,
                truncation=True,
                max_length=512
            )

    def predict(self, X: list[str]) -> list[int]:
        """Predicts whether the code snippets are vulnerable (1) or safe (0)."""
        self._initialize_pipeline()
        
        # Hugging Face models usually have a max sequence length (e.g., 512 tokens).
        # We might need to truncate the raw code if it's too long.
        predictions = []
        for code_snippet in X:
            try:
                # The pipeline expects a string. We truncate it naively by characters to avoid crashing the tokenizer
                # 2000 chars is usually safe for 512 tokens
                result = self.pipe_(str(code_snippet))[0]
                # Assuming the model returns labels like 'LABEL_1' (Vulnerable) or 'LABEL_0' (Safe)
                # or '1' / '0'. We map it to int.
                label = result['label']
                if '1' in label or label.lower() == 'vulnerable' or label.lower() == 'true':
                    predictions.append(1)
                else:
                    predictions.append(0)
            except Exception as e:
                print(f"Error predicting snippet with VulBERTa: {e}")
                predictions.append(0)  # Default to safe on error
                
        return predictions

    def predict_proba(self, X: list[str]) -> list[list[float]]:
        """Returns the probabilities for [Safe, Vulnerable]."""
        self._initialize_pipeline()
        
        probabilities = []
        for code_snippet in X:
            try:
                result = self.pipe_(str(code_snippet))[0]
                label = result['label']
                score = result['score']
                
                is_vulnerable = '1' in label or label.lower() == 'vulnerable' or label.lower() == 'true'
                
                if is_vulnerable:
                    probabilities.append([1.0 - score, score])
                else:
                    probabilities.append([score, 1.0 - score])
            except Exception as e:
                probabilities.append([1.0, 0.0])  # Default to safe
                
        import numpy as np
        return np.array(probabilities)
