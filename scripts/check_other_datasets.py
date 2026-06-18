#!/usr/bin/env python3
"""Check other datasets (CodeXGLUE, D2A) fields."""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

codexglue_path = project_root / "data/codexglue/train.jsonl"
if codexglue_path.exists():
    print("\n--- CodeXGLUE first 3 samples ---")
    import json
    with open(codexglue_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >=3:
                break
            obj = json.loads(line)
            print(f"\nSample {i+1} keys: {list(obj.keys())}")
            for k, v in list(obj.items())[:5]:  # Show first 5 fields
                print(f"  {k}: {v[:100] if isinstance(v, str) else v}...")

d2a_path = project_root / "data/d2a/train.jsonl"
if d2a_path.exists():
    print("\n--- D2A first 3 samples ---")
    import json
    with open(d2a_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >=3:
                break
            obj = json.loads(line)
            print(f"\nSample {i+1} keys: {list(obj.keys())}")
            for k, v in list(obj.items())[:5]:
                print(f"  {k}: {v[:100] if isinstance(v, str) else v}...")
