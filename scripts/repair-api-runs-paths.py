from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath


def normalize_prefix(value: str) -> str:
    return value.replace("\\", "/").rstrip("/")


def rewrite_path(value: str, old_root: str, new_root: str) -> str:
    normalized_value = value.replace("\\", "/")
    normalized_old_root = normalize_prefix(old_root)
    if not normalized_value.lower().startswith(normalized_old_root.lower()):
        return value

    suffix = normalized_value[len(normalized_old_root):].lstrip("/")
    return str(PurePosixPath(new_root) / suffix) if suffix else str(PurePosixPath(new_root))


def rewrite_json_value(value, old_root: str, new_root: str):
    if isinstance(value, dict):
        return {key: rewrite_json_value(inner, old_root, new_root) for key, inner in value.items()}
    if isinstance(value, list):
        return [rewrite_json_value(inner, old_root, new_root) for inner in value]
    if isinstance(value, str):
        return rewrite_path(value, old_root, new_root)
    return value


def build_text_path_pattern(old_root: str) -> re.Pattern[str]:
    normalized_old_root = normalize_prefix(old_root)
    root_pattern = re.escape(normalized_old_root).replace("/", r"[\\/]")
    return re.compile(rf"{root_pattern}(?P<suffix>(?:[\\/][^\s'\",]+)*)", re.IGNORECASE)


def rewrite_text_value(value: str, old_root: str, new_root: str) -> str:
    normalized_new_root = str(PurePosixPath(new_root))
    pattern = build_text_path_pattern(old_root)

    def replacer(match: re.Match[str]) -> str:
        suffix = match.group("suffix").replace("\\", "/")
        return normalized_new_root + suffix

    return pattern.sub(replacer, value)


def process_json_file(path: Path, old_root: str, new_root: str) -> bool:
    original_text = path.read_text(encoding="utf-8")
    payload = json.loads(original_text)
    updated = rewrite_json_value(payload, old_root, new_root)
    updated_text = json.dumps(updated, indent=2, ensure_ascii=False) + "\n"
    if updated_text == original_text:
        return False
    path.write_text(updated_text, encoding="utf-8")
    return True


def process_text_file(path: Path, old_root: str, new_root: str) -> bool:
    original_text = path.read_text(encoding="utf-8")
    updated_text = rewrite_text_value(original_text, old_root, new_root)
    if updated_text == original_text:
        return False
    path.write_text(updated_text, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Rewrite stored absolute paths inside api_runs.")
    parser.add_argument("--api-runs-root", required=True, help="Path to api_runs")
    parser.add_argument("--old-root", required=True, help="Old project root prefix")
    parser.add_argument("--new-root", required=True, help="New project root prefix")
    args = parser.parse_args()

    api_runs_root = Path(args.api_runs_root).resolve()
    if not api_runs_root.exists():
        raise SystemExit(f"api_runs root not found: {api_runs_root}")

    changed_files = 0

    for path in api_runs_root.rglob("*.json"):
        if process_json_file(path, args.old_root, args.new_root):
            changed_files += 1

    for suffix in ("*.yaml", "*.yml"):
        for path in api_runs_root.rglob(suffix):
            if process_text_file(path, args.old_root, args.new_root):
                changed_files += 1

    print(f"Rewrote paths in {changed_files} files under {api_runs_root}")


if __name__ == "__main__":
    main()
