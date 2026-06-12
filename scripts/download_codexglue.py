"""
Download CodeXGLUE Defect Detection dataset.
Uses HuggingFace datasets library with the correct namespace.
Dataset: google/code_x_glue_cc_defect_detection
"""
import sys
import subprocess
from pathlib import Path

def ensure_datasets():
    try:
        import datasets
    except ImportError:
        print("Installing 'datasets' library...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets"])

def download_codexglue():
    ensure_datasets()
    from datasets import load_dataset
    
    out_dir = Path("data/codexglue")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("Downloading CodeXGLUE defect detection dataset from HuggingFace...")
    dataset = load_dataset("google/code_x_glue_cc_defect_detection")
    
    for split in ["train", "validation", "test"]:
        if split in dataset:
            dest = out_dir / f"{split}.jsonl"
            print(f"Exporting {split} split ({len(dataset[split])} samples) -> {dest}")
            dataset[split].to_json(dest, orient="records", lines=True)
    
    print("\nDone! Train with: python -m app.interfaces.cli train --use-codexglue")

if __name__ == "__main__":
    download_codexglue()
