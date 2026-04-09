from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "literature_screening"
if str(PACKAGE_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from literature_screening.storage_paths import is_storage_absolute_path, normalize_relative_storage_path, to_stored_path


PATH_KEYS = frozenset({"path", "run_root", "output_dir"})
PATH_LIST_KEYS = frozenset({"uploaded_input_paths", "virtual_dataset_paths", "input_files"})


def relativize_storage_payload(payload: Any, *, api_runs_root: Path, parent_key: str | None = None) -> Any:
    if isinstance(payload, dict):
        return {
            key: relativize_storage_payload(value, api_runs_root=api_runs_root, parent_key=key)
            for key, value in payload.items()
        }

    if isinstance(payload, list):
        if parent_key in PATH_LIST_KEYS:
            return [relativize_storage_value(item, api_runs_root=api_runs_root) for item in payload]
        return [relativize_storage_payload(item, api_runs_root=api_runs_root) for item in payload]

    if parent_key in PATH_KEYS:
        return relativize_storage_value(payload, api_runs_root=api_runs_root)

    return payload


def relativize_storage_value(value: Any, *, api_runs_root: Path) -> Any:
    if not isinstance(value, str):
        return value

    rewritten = to_stored_path(value, storage_root=api_runs_root)
    if rewritten != value or not is_storage_absolute_path(value):
        return rewritten

    normalized = value.replace("\\", "/")
    marker = f"/{api_runs_root.name}/"
    marker_index = normalized.lower().rfind(marker.lower())
    if marker_index == -1:
        return value

    suffix = normalized[marker_index + len(marker):]
    return normalize_relative_storage_path(suffix)


def process_json_file(path: Path, *, api_runs_root: Path) -> bool:
    payload = json.loads(path.read_text(encoding="utf-8"))
    updated = relativize_storage_payload(payload, api_runs_root=api_runs_root)
    if updated == payload:
        return False
    path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def process_yaml_file(path: Path, *, api_runs_root: Path) -> bool:
    raw_text = path.read_text(encoding="utf-8")
    payload = yaml.safe_load(raw_text)
    if payload is None:
        return False
    updated = relativize_storage_payload(payload, api_runs_root=api_runs_root)
    if updated == payload:
        return False
    path.write_text(yaml.safe_dump(updated, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Rewrite stored api_runs paths to be relative to api_runs root.")
    parser.add_argument("--api-runs-root", required=True, help="Path to api_runs")
    args = parser.parse_args()

    api_runs_root = Path(args.api_runs_root).resolve()
    if not api_runs_root.exists():
        raise SystemExit(f"api_runs root not found: {api_runs_root}")

    changed_files = 0
    for path in api_runs_root.rglob("*.json"):
        if process_json_file(path, api_runs_root=api_runs_root):
            changed_files += 1
    for suffix in ("*.yaml", "*.yml"):
        for path in api_runs_root.rglob(suffix):
            if process_yaml_file(path, api_runs_root=api_runs_root):
                changed_files += 1

    print(f"Rewrote {changed_files} files under {api_runs_root}")


if __name__ == "__main__":
    main()
