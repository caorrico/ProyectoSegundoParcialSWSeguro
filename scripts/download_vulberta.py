"""
Download and prepare VulBERTa dataset for integration into our pipeline.

The VulBERTa dataset is hosted on OneDrive by Imperial College London.
Link: https://1drv.ms/u/s!AueKnGqzBuIVkq4B9ESELGQ-VtjIYA?e=f0moEm

Since direct download from OneDrive requires browser interaction,
this script provides instructions and then processes the downloaded zip.
"""
import json
import sys
import zipfile
from pathlib import Path

DATA_DIR = Path("data/vulberta")


def process_vulberta_zip(zip_path: Path):
    """Extract and convert the VulBERTa zip into our JSONL format."""
    print(f"[INFO] Extracting {zip_path} ...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(DATA_DIR)
    print(f"[INFO] Extracted to {DATA_DIR}")

    # VulBERTa dataset structure: data/finetune/{dataset_name}/{train,valid,test}.jsonl
    # Each line: {"func": "...", "target": 0|1}
    finetune_dir = None
    for candidate in [
        DATA_DIR / "finetune",
        DATA_DIR / "data" / "finetune",
    ]:
        if candidate.exists():
            finetune_dir = candidate
            break

    if finetune_dir is None:
        # Search recursively for any .jsonl files
        jsonl_files = list(DATA_DIR.rglob("*.jsonl"))
        if not jsonl_files:
            print("[WARN] No .jsonl files found. Listing extracted contents:")
            for f in sorted(DATA_DIR.rglob("*")):
                print(f"  {f}")
            return
        print(f"[INFO] Found {len(jsonl_files)} .jsonl files")
        # Merge all into one train.jsonl
        output = DATA_DIR / "train.jsonl"
        count = 0
        with open(output, "w", encoding="utf-8") as out:
            for jf in jsonl_files:
                with open(jf, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            code = record.get("func", record.get("code", record.get("processed_func", "")))
                            label = record.get("target", record.get("label", record.get("is_vulnerable", -1)))
                            if code and label in (0, 1):
                                out.write(json.dumps({"raw_code": code, "is_vulnerable": label}) + "\n")
                                count += 1
                        except json.JSONDecodeError:
                            continue
        print(f"[OK] Wrote {count} samples to {output}")
        return

    # Process structured finetune directory
    output = DATA_DIR / "train.jsonl"
    count = 0
    with open(output, "w", encoding="utf-8") as out:
        for dataset_dir in sorted(finetune_dir.iterdir()):
            if not dataset_dir.is_dir():
                continue
            print(f"[INFO] Processing VulBERTa finetune dataset: {dataset_dir.name}")
            for split_file in sorted(dataset_dir.glob("*.jsonl")):
                with open(split_file, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            code = record.get("func", record.get("code", ""))
                            label = record.get("target", record.get("label", -1))
                            if code and label in (0, 1):
                                out.write(json.dumps({"raw_code": code, "is_vulnerable": label}) + "\n")
                                count += 1
                        except json.JSONDecodeError:
                            continue

    print(f"[OK] Wrote {count} samples to {output}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        zip_path = Path(sys.argv[1])
    else:
        zip_path = Path("data/vulberta/data.zip")

    if not zip_path.exists():
        print("=" * 60)
        print("VulBERTa Dataset Download Instructions")
        print("=" * 60)
        print()
        print("The VulBERTa dataset is hosted on OneDrive.")
        print("Please download it manually:")
        print()
        print("  1. Open this link in your browser:")
        print("     https://1drv.ms/u/s!AueKnGqzBuIVkq4B9ESELGQ-VtjIYA?e=f0moEm")
        print()
        print("  2. Click 'Download' to get data.zip")
        print()
        print(f"  3. Save/move the file to: {zip_path.resolve()}")
        print()
        print("  4. Run this script again:")
        print(f"     python {sys.argv[0]}")
        print()
        print("  Or specify the path directly:")
        print(f"     python {sys.argv[0]} <path_to_data.zip>")
        print("=" * 60)
        sys.exit(1)

    process_vulberta_zip(zip_path)
