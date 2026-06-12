from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.domain.entities import RawCodeModule
from app.infrastructure.ml.random_forest_predictor import RandomForestPredictor

def main():
    # Use the model trained with CVEFixes
    model_path = PROJECT_ROOT / "models" / "cvefixes_vulnerability_model.joblib"
    if not model_path.exists():
        print(f"Model not found at {model_path}. Please run scripts/train_cvefixes.py first.")
        return

    predictor = RandomForestPredictor(model_path)

    # Sample code to predict (vulnerable)
    sample_path = PROJECT_ROOT / "examples" / "vulnerable_sample.cpp"
    if not sample_path.exists():
        print(f"Sample not found at {sample_path}")
        return
        
    code = sample_path.read_text(encoding="utf-8")
    raw_module = RawCodeModule(raw_code=code)

    print(f"Predicting vulnerability for: {sample_path.name}")
    is_vulnerable, probability = predictor.predict(raw_module)
    
    print(f"Vulnerable: {is_vulnerable}")
    print(f"Probability: {probability:.4f}")

    # Generate SHAP explanation
    report_path = PROJECT_ROOT / "reports" / "cvefixes_shap_explanation.html"
    print(f"Generating SHAP explanation report at: {report_path}...")
    predictor.generate_explanation(raw_module, report_path)
    
    # Get top features from SHAP
    top_features = predictor.get_top_features(raw_module)
    print(f"Top contributing features (SHAP): {top_features}")

    print("SUCCESS: Prediction and SHAP report generated.")

if __name__ == "__main__":
    main()
