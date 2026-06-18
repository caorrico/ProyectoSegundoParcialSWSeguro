from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


CODE_FIELDS = (
    "raw_code",
    "func",
    "code",
    "functionSource",
    "function",
    "vulnerable_code",
    "fixed_code",
)
LABEL_FIELDS = ("is_vulnerable", "target", "label", "vulnerable", "safety")
MIN_CODE_CHARS = 30
MAX_CODE_CHARS = 200_000


@dataclass
class DatasetBuildResult:
    frame: pd.DataFrame
    profile: dict[str, Any]


def build_clean_training_frame(
    base_dir: Path,
    max_records_per_source: int | None = None,
    include_cvefixes: bool = True,
) -> DatasetBuildResult:
    records: list[dict[str, Any]] = []
    profile: dict[str, Any] = {}

    for source_name, paths in _dataset_paths(base_dir, include_cvefixes).items():
        source_records = []
        errors = 0
        for path in paths:
            try:
                for raw in _iter_records(path):
                    source_records.extend(normalize_records(raw, source_name, path))
                    if max_records_per_source and len(source_records) >= max_records_per_source:
                        break
            except Exception as error:
                errors += 1
                profile[f"{source_name}:{path.name}:error"] = str(error)
            if max_records_per_source and len(source_records) >= max_records_per_source:
                break

        cleaned = clean_records(source_records)
        profile[source_name] = {
            "input_records": len(source_records),
            "usable_records": len(cleaned),
            "label_counts": Counter(row["is_vulnerable"] for row in cleaned),
            "paths": [str(path) for path in paths],
            "errors": errors,
        }
        records.extend(cleaned)

    frame = pd.DataFrame(records)
    if frame.empty:
        raise RuntimeError("No usable vulnerability training records were found.")

    before_dedup = len(frame)
    frame = frame.drop_duplicates(subset=["code_hash"]).reset_index(drop=True)
    profile["combined"] = {
        "before_dedup": before_dedup,
        "after_dedup": len(frame),
        "label_counts": frame["is_vulnerable"].value_counts().to_dict(),
        "source_counts": frame["source"].value_counts().to_dict(),
    }
    return DatasetBuildResult(frame=frame, profile=profile)


def clean_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned = []
    for record in records:
        code = _clean_code(str(record["raw_code"]))
        if len(code) < MIN_CODE_CHARS or len(code) > MAX_CODE_CHARS:
            continue
        label = _normalize_label(record["is_vulnerable"])
        if label not in (0, 1):
            continue
        cleaned.append(
            {
                "raw_code": code,
                "is_vulnerable": label,
                "source": record["source"],
                "path": record["path"],
                "language": _normalize_language(record.get("language"), code),
                "group_id": str(record.get("group_id") or ""),
                "code_hash": _stable_hash(code),
                "code_length": len(code),
                "line_count": len([line for line in code.splitlines() if line.strip()]),
            }
        )
    return cleaned


def normalize_records(raw: dict[str, Any], source: str, path: Path) -> list[dict[str, Any]]:
    if source.startswith("megavul"):
        records = []
        cve_id = raw.get("cve_id") or ""
        for commit in raw.get("commits", []) or []:
            commit_id = commit.get("commit_hash") or commit.get("id") or cve_id
            for file_item in commit.get("files", []) or []:
                language = file_item.get("language") or ""
                for index, function in enumerate(file_item.get("vulnerable_functions", []) or []):
                    group_id = f"{cve_id}:{commit_id}:{file_item.get('file_path', '')}:{function.get('func_name', index)}"
                    func_before = function.get("func_before") or function.get("before")
                    if isinstance(func_before, str) and func_before.strip():
                        records.append(
                            _standard_record(func_before, 1, source, path, language, group_id)
                        )
                    func_after = function.get("func_after") or function.get("func") or function.get("after")
                    if isinstance(func_after, str) and func_after.strip():
                        records.append(
                            _standard_record(func_after, 0, source, path, language, group_id)
                        )
                for index, function in enumerate(file_item.get("non_vulnerable_functions", []) or []):
                    group_id = f"{cve_id}:{commit_id}:{file_item.get('file_path', '')}:non_vul:{index}"
                    func = function.get("func")
                    if isinstance(func, str) and func.strip():
                        records.append(_standard_record(func, 0, source, path, language, group_id))
        return records

    if source == "cvefixes_zip":
        code = raw.get("code")
        label = raw.get("safety")
    else:
        code = _first_nonempty(raw, CODE_FIELDS)
        label = _first_present(raw, LABEL_FIELDS)

    if code is None or label is None:
        return []
    group_id = _first_present(raw, ("cve_id", "commit_id", "id", "hash", "project"))
    return [_standard_record(code, label, source, path, raw.get("language"), group_id)]


def _standard_record(
    code: Any,
    label: Any,
    source: str,
    path: Path,
    language: Any = "",
    group_id: Any = "",
) -> dict[str, Any]:
    return {
        "raw_code": code,
        "is_vulnerable": label,
        "source": source,
        "path": str(path),
        "language": language or "",
        "group_id": group_id or "",
    }


def _dataset_paths(base_dir: Path, include_cvefixes: bool) -> dict[str, list[Path]]:
    paths = {
        "codexglue": sorted((base_dir / "data" / "codexglue").glob("*.jsonl")),
        "d2a": sorted((base_dir / "data" / "d2a").glob("*.jsonl")),
        "reveal": sorted((base_dir / "data" / "reveal").glob("*.jsonl")),
        "megavul_java": sorted((base_dir / "data" / "megavul" / "java").glob("*.json")),
        "megavul_c_cpp": sorted((base_dir / "data" / "megavul" / "c_cpp").glob("*.json")),
        "owasp2025": sorted((base_dir / "data" / "owasp2025").glob("*.jsonl")),
    }
    cvefixes_zip = base_dir / "data" / "data" / "CVEFixes.csv.zip"
    if include_cvefixes and cvefixes_zip.exists():
        paths["cvefixes_zip"] = [cvefixes_zip]
    return {key: [path for path in value if path.exists()] for key, value in paths.items()}


def _iter_records(path: Path) -> Iterable[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        with path.open(encoding="utf-8", errors="replace") as file:
            for line in file:
                if line.strip():
                    yield json.loads(line)
        return

    if path.suffix.lower() == ".json":
        import ijson

        with path.open("rb") as file:
            yield from ijson.items(file, "item")
        return

    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
            for csv_name in csv_names:
                with archive.open(csv_name) as raw_file:
                    text_file = io.TextIOWrapper(raw_file, encoding="utf-8", errors="replace", newline="")
                    yield from csv.DictReader(text_file)
        return

    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8", errors="replace", newline="") as file:
            yield from csv.DictReader(file)


def _first_nonempty(raw: dict[str, Any], fields: tuple[str, ...]) -> Any:
    for field in fields:
        value = raw.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _first_present(raw: dict[str, Any], fields: tuple[str, ...]) -> Any:
    for field in fields:
        if field in raw and raw[field] is not None:
            return raw[field]
    return None


def _normalize_label(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value if value in (0, 1) else None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "vulnerable", "unsafe", "buggy"}:
        return 1
    if text in {"0", "false", "no", "safe", "fixed", "clean"}:
        return 0
    return None


def _normalize_language(value: Any, code: str) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("c++", "cpp").replace("c/cpp", "cpp").replace("c_cpp", "cpp")
    aliases = {
        "c": "c",
        "cpp": "cpp",
        "cc": "cpp",
        "cxx": "cpp",
        "h": "cpp",
        "hpp": "cpp",
        "java": "java",
        "py": "python",
        "python": "python",
        "js": "javascript",
        "javascript": "javascript",
        "ts": "typescript",
        "typescript": "typescript",
        "php": "php",
        "go": "go",
        "golang": "go",
        "html": "html",
    }
    if text in aliases:
        return aliases[text]
    return _detect_language(code)


def _clean_code(code: str) -> str:
    code = code.replace("\x00", "")
    code = code.replace("\r\n", "\n").replace("\r", "\n")
    code = re.sub(r"(?im)(//|#|/\*)\s*(vulnerable|safe)\s*:?", r"\1 ", code)
    code = re.sub(r"(?i)\b(vulnerable|safe)\s*:\s*", "", code)
    code = re.sub(r"[ \t]+", " ", code)
    code = re.sub(r"\n{4,}", "\n\n\n", code)
    return code.strip()


def _detect_language(code: str) -> str:
    if re.search(r"\b(public\s+class|import\s+java|package\s+[\w.]+;)", code):
        return "java"
    if re.search(r"#include\s*<|std::|->", code):
        return "cpp"
    if re.search(r"\bdef\s+\w+\(|import\s+\w+", code):
        return "python"
    if re.search(r"\bfunction\s+\w+\(|const\s+\w+\s*=", code):
        return "javascript"
    return "unknown"


def _stable_hash(code: str) -> str:
    import hashlib

    return hashlib.sha256(code.encode("utf-8", errors="ignore")).hexdigest()
