from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


STORED_PATH_KEYS = frozenset({"path", "run_root", "output_dir"})
STORED_PATH_LIST_KEYS = frozenset({"uploaded_input_paths", "virtual_dataset_paths", "input_files"})
API_RUNS_TOP_LEVEL_DIRS = frozenset({"projects", "tasks", "runs", "templates"})


def is_storage_absolute_path(value: str | Path) -> bool:
    text = str(value).strip()
    if not text:
        return False
    return PurePosixPath(text).is_absolute() or PureWindowsPath(text).is_absolute()


def normalize_relative_storage_path(value: str | Path) -> str:
    return PurePosixPath(str(value).strip().replace("\\", "/")).as_posix()


def to_stored_path(value: str | Path | None, *, storage_root: Path) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return text

    if not is_storage_absolute_path(text):
        return normalize_relative_storage_path(text)

    try:
        relative_path = Path(text).resolve().relative_to(storage_root.resolve())
    except Exception:
        return text
    return relative_path.as_posix()


def resolve_stored_path(value: str | Path | None, *, storage_root: Path) -> Path | None:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    if is_storage_absolute_path(text):
        remapped = _remap_foreign_api_runs_absolute_path(text, storage_root=storage_root)
        if remapped is not None:
            return remapped
        return Path(text)

    return storage_root / Path(PurePosixPath(normalize_relative_storage_path(text)))


def rewrite_storage_payload(payload: Any, *, storage_root: Path, mode: str, parent_key: str | None = None) -> Any:
    if isinstance(payload, dict):
        return {
            key: rewrite_storage_payload(value, storage_root=storage_root, mode=mode, parent_key=key)
            for key, value in payload.items()
        }

    if isinstance(payload, list):
        if parent_key in STORED_PATH_LIST_KEYS:
            return [_rewrite_storage_scalar(item, storage_root=storage_root, mode=mode) for item in payload]
        return [rewrite_storage_payload(item, storage_root=storage_root, mode=mode) for item in payload]

    if parent_key in STORED_PATH_KEYS:
        return _rewrite_storage_scalar(payload, storage_root=storage_root, mode=mode)

    return payload


def find_named_ancestor(path: Path, *, name: str) -> Path | None:
    resolved = path.resolve()
    for candidate in (resolved, *resolved.parents):
        if candidate.name == name:
            return candidate
    return None


def resolve_config_path(value: str, *, config_dir: Path, storage_root: Path | None = None) -> str:
    if is_storage_absolute_path(value):
        return value

    normalized = normalize_relative_storage_path(value)
    path_parts = PurePosixPath(normalized).parts
    if storage_root is not None and path_parts and path_parts[0] in API_RUNS_TOP_LEVEL_DIRS:
        return str(storage_root / Path(PurePosixPath(normalized)))
    return str((config_dir / Path(PurePosixPath(normalized))).resolve())


def _rewrite_storage_scalar(value: Any, *, storage_root: Path, mode: str) -> Any:
    if not isinstance(value, (str, Path)):
        return value

    if mode == "dehydrate":
        return to_stored_path(value, storage_root=storage_root)
    if mode == "hydrate":
        resolved = resolve_stored_path(value, storage_root=storage_root)
        return str(resolved) if resolved is not None else value

    raise ValueError(f"Unsupported storage rewrite mode: {mode}")


def _remap_foreign_api_runs_absolute_path(value: str, *, storage_root: Path) -> Path | None:
    """Map an absolute path from another workspace into the current storage root.

    This supports Windows absolute paths like:
      E:\\old\\literature_screening\\data\\api_runs\\tasks\\<id>\\...
    which are not accessible inside the container, but whose data has been migrated to the
    current storage root (e.g. storage_root/tasks/<id>/...).
    """
    text = str(value).strip()
    if not text:
        return None

    try:
        parts = PureWindowsPath(text).parts if PureWindowsPath(text).is_absolute() else PurePosixPath(text).parts
    except Exception:
        return None

    lowered = [part.lower() for part in parts]
    if "api_runs" not in lowered:
        return None
    api_index = lowered.index("api_runs")
    if api_index + 1 >= len(parts):
        return None

    suffix_parts = [part for part in parts[api_index + 1 :] if part not in ("/", "\\")]
    if not suffix_parts:
        return None
    top = suffix_parts[0].replace("\\", "/").strip("/")
    if top not in API_RUNS_TOP_LEVEL_DIRS:
        return None

    candidate = storage_root / Path(PurePosixPath("/".join([p.replace("\\", "/") for p in suffix_parts])))
    if candidate.exists() or candidate.parent.exists():
        return candidate
    return None
