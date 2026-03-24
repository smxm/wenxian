from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


class TemplateStore:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.templates_dir = root_dir / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def list_templates(self, project_id: str | None = None) -> list[dict[str, Any]]:
        templates = [self._read(path) for path in self.templates_dir.glob("*.json")]
        if project_id is not None:
            templates = [item for item in templates if item.get("project_id") in {None, project_id}]
        templates.sort(key=lambda item: item["updated_at"], reverse=True)
        return templates

    def create_template(
        self,
        *,
        name: str,
        payload: dict[str, Any],
        project_id: str | None = None,
        scope: str = "project",
    ) -> dict[str, Any]:
        template_id = uuid.uuid4().hex[:12]
        now = datetime.now().astimezone().isoformat()
        template = {
            "id": template_id,
            "project_id": project_id,
            "name": name,
            "scope": scope if project_id else "global",
            "payload": payload,
            "created_at": now,
            "updated_at": now,
        }
        self._write(self.templates_dir / f"{template_id}.json", template)
        return template

    @staticmethod
    def _read(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
