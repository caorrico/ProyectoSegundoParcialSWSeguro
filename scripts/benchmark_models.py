"""
Benchmark script to compare multiple ML algorithms for vulnerability prediction.
"""
import sys
import time
from pathlib import Path
from tabulate import tabulate

from app.application.use_cases.train_vulnerability_model import TrainVulnerabilityModelUseCase
from app.infrastructure.repositories.combined_dataset_repository import CombinedDatasetRepository
from app.infrastructure.ml.random_forest_trainer import RandomForestTrainer
from app.infrastructure.ml.xgboost_trainer import XGBoostTrainer
from app.infrastructure.ml.lightgbm_trainer import LightGBMTrainer
from app.infrastructure.ml.svm_trainer import SVMTrainer


def main():
    print("=" * 60)
    print(" ML Algorithm Benchmarking for Vulnerability Prediction")
    print("=" * 60)
    print("Loading datasets...")
    # Limiting the dataset specifically because SVM is very slow to train on TF-IDF
    repository = CombinedDatasetRepository(limit_per_source=800)
    
    try:
        dataset = repository.load()
    except Exception as e:
        print(f"Error loading datasets: {e}")
        sys.exit(1)
        
    print(f"Total samples for benchmarking: {len(dataset)}")
    print("-" * 60)

    # Output paths (we use dummy paths so we don't overwrite production models)
    base_model_path = Path("models/benchmark")
    base_report_path = Path("reports/benchmark")

    trainers = {
        "Random Forest": RandomForestTrainer(
            model_path=base_model_path / "rf.joblib",
            report_path=base_report_path / "rf_metrics.json"
        ),
        "XGBoost": XGBoostTrainer(
            model_path=base_model_path / "xgb.joblib",
            report_path=base_report_path / "xgb_metrics.json"
        ),
        "LightGBM": LightGBMTrainer(
            model_path=base_model_path / "lgb.joblib",
            report_path=base_report_path / "lgb_metrics.json"
        ),
        "SVM": SVMTrainer(
            model_path=base_model_path / "svm.joblib",
            report_path=base_report_path / "svm_metrics.json"
        ),
    }

    results = []

    for name, trainer in trainers.items():
        print(f"Training {name}...")
        start_time = time.time()
        
        use_case = TrainVulnerabilityModelUseCase(repository, trainer)
        
        try:
            metrics = use_case.execute()
            duration = time.time() - start_time
            print(f"  -> Finished in {duration:.2f}s")
            
            results.append([
                name,
                metrics["accuracy"],
                metrics["precision"],
                metrics["recall"],
                metrics["f1_score"],
                metrics["roc_auc"],
                metrics["cross_validation_f1_mean"],
                f"{duration:.1f}s"
            ])
            
        except Exception as e:
            print(f"  -> Error training {name}: {e}")
            results.append([name, "ERROR", "ERROR", "ERROR", "ERROR", "ERROR", "ERROR", "ERROR"])

    print("\n\n")
    print("=" * 80)
    print(" BENCHMARK RESULTS")
    print("=" * 80)
    headers = ["Algorithm", "Accuracy", "Precision", "Recall", "F1 Score", "ROC AUC", "CV F1 Mean", "Time"]
    print(tabulate(results, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    main()
