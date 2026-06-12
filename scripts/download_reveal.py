"""
Download ReVeal vulnerability detection dataset.
HuggingFace: claudios/ReVeal
Contains C/C++ code from Chromium and Debian projects.
"""
import sys
import os
import subprocess
from pathlib import Path

def write_progress(msg):
    print(msg, flush=True)
    with open("download_progress.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def ensure_datasets():
    write_progress("Checking if 'datasets' library is installed...")
    try:
        import datasets
        write_progress("datasets library is already installed.")
    except ImportError:
        write_progress("Installing 'datasets' library via pip...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            write_progress("datasets library installed successfully.")
        except Exception as e:
            write_progress(f"Failed to install datasets: {str(e)}")
            raise

def download_reveal():
    try:
        if os.path.exists("download_progress.log"):
            os.remove("download_progress.log")
    except:
        pass

    write_progress("Starting download process...")
    ensure_datasets()
    
    write_progress("Importing datasets library...")
    from datasets import load_dataset

    out_dir = Path("data/reveal")
    out_dir.mkdir(parents=True, exist_ok=True)

    write_progress("Loading claudios/ReVeal from Hugging Face...")
    try:
        dataset = load_dataset("claudios/ReVeal")
        write_progress(f"Dataset loaded successfully! Splits found: {list(dataset.keys())}")
        
        for split in dataset:
            dest = out_dir / f"{split}.jsonl"
            write_progress(f"Exporting {split} split ({len(dataset[split])} samples) -> {dest}...")
            dataset[split].to_json(dest, orient="records", lines=True)
            write_progress(f"Exported {split} split successfully.")

        write_progress("SUCCESS: All splits exported to data/reveal.")
    except Exception as e:
        write_progress(f"ERROR during download/export: {str(e)}")
        import traceback
        write_progress(traceback.format_exc())

if __name__ == "__main__":
    download_reveal()
