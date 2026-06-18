from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.infrastructure.ml.code_feature_extractor import extract_code_features  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract static security features from source code.")
    parser.add_argument("files", nargs="+", help="Source files to inspect")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    results = []
    for file_name in args.files:
        path = Path(file_name)
        code = path.read_text(encoding="utf-8", errors="replace")
        results.append(extract_code_features(code, path).to_dict())

    payload = {"files": results}
    text = json.dumps(payload, indent=2)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
