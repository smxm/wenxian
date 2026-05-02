from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from jsonschema import ValidationError, validate

from literature_screening.core.exceptions import ConfigValidationError
from literature_screening.core.models import RunConfig
from literature_screening.core.schema import RUN_CONFIG_SCHEMA
from literature_screening.storage_paths import find_named_ancestor, resolve_config_path


def load_yaml_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ConfigValidationError("Configuration root must be a mapping.")
    return data


def load_run_config(path: Path) -> RunConfig:
    if not path.exists():
        raise ConfigValidationError(f"Config file not found: {path}")

    raw_config = load_yaml_file(path)

    if "input" in raw_config and isinstance(raw_config["input"], dict):
        input_section = raw_config["input"]
        if "input_files" not in input_section and "bib_files" in input_section:
            input_section["input_files"] = input_section["bib_files"]
        input_section.pop("bib_files", None)

    try:
        validate(instance=raw_config, schema=RUN_CONFIG_SCHEMA)
    except ValidationError as exc:
        raise ConfigValidationError(f"Configuration schema validation failed: {exc.message}") from exc

    config_dir = path.parent.resolve()
    storage_root = find_named_ancestor(config_dir, name="api_runs")

    if "input" in raw_config and "input_files" in raw_config["input"]:
        raw_config["input"]["input_files"] = [
            resolve_config_path(input_file, config_dir=config_dir, storage_root=storage_root)
            for input_file in raw_config["input"]["input_files"]
        ]

    if "project" in raw_config and "output_dir" in raw_config["project"]:
        output_dir = raw_config["project"]["output_dir"]
        raw_config["project"]["output_dir"] = resolve_config_path(
            output_dir,
            config_dir=config_dir,
            storage_root=storage_root,
        )

    try:
        return RunConfig.model_validate(raw_config)
    except Exception as exc:
        raise ConfigValidationError(f"Configuration model validation failed: {exc}") from exc
