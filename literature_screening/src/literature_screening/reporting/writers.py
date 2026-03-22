from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel


def _serialize(data: dict | list | BaseModel | object) -> object:
    if isinstance(data, BaseModel):
        return data.model_dump(mode="json")
    if isinstance(data, list):
        return [_serialize(item) for item in data]
    if isinstance(data, dict):
        return {key: _serialize(value) for key, value in data.items()}
    return data


def write_json(data: dict | list | BaseModel, output_path: Path) -> None:
    payload = _serialize(data)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
