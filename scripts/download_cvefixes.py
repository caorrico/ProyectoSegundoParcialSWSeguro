"""
Download CVEFixes vulnerability detection dataset.
HuggingFace: starsofchance/CVEfixes_v1.0.8
"""
import sys
import subprocess
from pathlib import Path
import importlib.util

def write_progress(msg):
    print(msg, flush=True)

def ensure_datasets():
    write_progress("Checking if 'datasets' library is installed...")
    if importlib.util.find_spec("datasets") is not None:
        write_progress("datasets library is already installed.")
        return
    write_progress("Installing 'datasets' library via pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        write_progress("datasets library installed successfully.")
    except Exception as e:
        write_progress(f"Failed to install datasets: {str(e)}")
        raise

def download_cvefixes():
    write_progress("Starting download process for CVEFixes...")
    ensure_datasets()
    
    from datasets import load_dataset

    out_dir = Path("data/cvefixes")
    out_dir.mkdir(parents=True, exist_ok=True)

    write_progress("Loading hitoshura25/cvefixes from Hugging Face...")
    try:
        # Load the dataset
        dataset = load_dataset("hitoshura25/cvefixes")
        write_progress(f"Dataset loaded successfully! Splits found: {list(dataset.keys())}")
        
        for split in dataset:
            dest = out_dir / f"{split}.jsonl"
            write_progress(f"Exporting {split} split ({len(dataset[split])} samples) -> {dest}...")
            dataset[split].to_json(dest, orient="records", lines=True)
            write_progress(f"Exported {split} split successfully.")

        write_progress("SUCCESS: All splits exported to data/cvefixes.")
    except Exception as e:
        write_progress(f"ERROR during download/export: {str(e)}")

if __name__ == "__main__":
    download_cvefixes()
