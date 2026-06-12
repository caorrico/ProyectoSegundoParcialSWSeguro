from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.shared.settings import settings
from app.infrastructure.repositories.cvefixes_dataset_repository import CVEFixesDatasetRepository
from app.infrastructure.ml.random_forest_trainer import RandomForestTrainer
from app.application.use_cases.train_vulnerability_model import TrainVulnerabilityModelUseCase

def main():
    print("Training model with CVEFixes dataset...")
    
    # Path to the downloaded CVEFixes dataset
    cvefixes_path = PROJECT_ROOT / "data" / "cvefixes" / "train.jsonl"
    
    # We'll use a limit of samples for this session to keep it manageable
    limit = 500 
    
    repository = CVEFixesDatasetRepository(cvefixes_path, limit=limit)
    
    # We want to save the model specifically for CVEFixes if we want to distinguish it, 
    # but the user said "usar cve fixes dataset", so we'll replace the main model.
    model_path = settings.base_dir / "models" / "cvefixes_vulnerability_model.joblib"
    report_path = settings.base_dir / "reports" / "cvefixes_metrics.json"
    
    trainer = RandomForestTrainer(
        model_path=model_path,
        report_path=report_path,
        random_state=settings.random_state
    )
    
    use_case = TrainVulnerabilityModelUseCase(repository, trainer)
    
    print("Loading and training (this might take a minute)...")
    metrics = use_case.execute(tune=False)
    
    print("Training complete!")
    print(f"Metrics: {metrics}")
    print(f"Model saved to: {model_path}")
    print(f"Report saved to: {report_path}")

if __name__ == "__main__":
    main()
