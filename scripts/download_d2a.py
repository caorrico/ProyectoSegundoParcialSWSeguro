"""
Download D2A (Differential Dataset Analysis) vulnerability dataset from IBM.
HuggingFace: claudios/D2A
Contains real-world C/C++ code from OpenSSL, FFmpeg, HTTPD, NGINX, Libtiff, Libav.
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

def download_d2a():
    ensure_datasets()
    from datasets import load_dataset
    
    out_dir = Path("data/d2a")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("Downloading D2A (IBM) vulnerability dataset from HuggingFace...")
    print("Using 'function' task (contains full function code + label)...")
    dataset = load_dataset("claudios/D2A", "function")
    
    for split in dataset:
        dest = out_dir / f"{split}.jsonl"
        print(f"Exporting {split} split ({len(dataset[split])} samples) -> {dest}")
        dataset[split].to_json(dest, orient="records", lines=True)
    
    print("\nDone! Train with: python -m app.interfaces.cli train --use-d2a")

if __name__ == "__main__":
    download_d2a()
