from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from literature_screening.bibtex.deduper import deduplicate_records
from literature_screening.bibtex.exporter import export_ris
from literature_screening.bibtex.parser import parse_bibtex_files


class WorkspaceStore:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.projects_dir = root_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def create_project(self, *, name: str, topic: str, description: str | None = None) -> dict[str, Any]:
        project_id = uuid.uuid4().hex[:12]
        now = datetime.now().astimezone().isoformat()
        payload = {
            "id": project_id,
            "name": name,
            "topic": topic,
            "description": description or "",
            "created_at": now,
            "updated_at": now,
        }
        project_root = self._project_root(project_id)
        (project_root / "datasets").mkdir(parents=True, exist_ok=True)
        (project_root / "derived").mkdir(parents=True, exist_ok=True)
        self._write(project_root / "project.json", payload)
        return payload

    def list_projects(self) -> list[dict[str, Any]]:
        projects: list[dict[str, Any]] = []
        for path in sorted(self.projects_dir.glob("*/project.json")):
            project = self._read(path)
            project_id = project["id"]
            project["dataset_count"] = len(self.list_project_datasets(project_id))
            projects.append(project)
        projects.sort(key=lambda item: item["updated_at"], reverse=True)
        return projects

    def load_project(self, project_id: str) -> dict[str, Any]:
        return self._read(self._project_root(project_id) / "project.json")

    def update_project(self, project_id: str, **changes: Any) -> dict[str, Any]:
        path = self._project_root(project_id) / "project.json"
        payload = self._read(path)
        payload.update(changes)
        payload["updated_at"] = datetime.now().astimezone().isoformat()
        self._write(path, payload)
        return payload

    def delete_project(self, project_id: str) -> None:
        project_root = self._project_root(project_id)
        if project_root.exists():
            shutil.rmtree(project_root)

    def list_project_datasets(self, project_id: str) -> list[dict[str, Any]]:
        datasets_dir = self._project_root(project_id) / "datasets"
        if not datasets_dir.exists():
            return []
        datasets = [self._read(path) for path in datasets_dir.glob("*.json")]
        datasets.sort(key=lambda item: item["created_at"], reverse=True)
        return datasets

    def load_dataset(self, project_id: str, dataset_id: str) -> dict[str, Any]:
        return self._read(self._project_root(project_id) / "datasets" / f"{dataset_id}.json")

    def find_dataset(self, dataset_id: str) -> dict[str, Any] | None:
        for path in self.projects_dir.glob(f"*/datasets/{dataset_id}.json"):
            return self._read(path)
        return None

    def register_dataset(
        self,
        *,
        project_id: str,
        task_id: str | None,
        kind: str,
        label: str,
        path: Path,
        record_count: int | None,
        file_format: str,
        source_dataset_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        dataset_id: str | None = None,
    ) -> dict[str, Any]:
        dataset_id = dataset_id or uuid.uuid4().hex[:12]
        now = datetime.now().astimezone().isoformat()
        payload = {
            "id": dataset_id,
            "project_id": project_id,
            "task_id": task_id,
            "kind": kind,
            "label": label,
            "path": str(path),
            "filename": path.name,
            "format": file_format,
            "record_count": record_count,
            "source_dataset_ids": source_dataset_ids or [],
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
        }
        dataset_path = self._project_root(project_id) / "datasets" / f"{dataset_id}.json"
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        self._write(dataset_path, payload)
        self.update_project(project_id)
        return payload

    def rebuild_cumulative_included_dataset(self, project_id: str) -> dict[str, Any] | None:
        datasets = [item for item in self.list_project_datasets(project_id) if item["kind"] == "included"]
        paths = [Path(item["path"]) for item in datasets if Path(item["path"]).exists()]
        if not paths:
            return None

        records = parse_bibtex_files(paths, encoding="auto")
        deduped = deduplicate_records(records)
        derived_dir = self._project_root(project_id) / "derived"
        derived_dir.mkdir(parents=True, exist_ok=True)
        output_path = derived_dir / "cumulative_included.ris"
        export_ris(deduped, output_path)
        return self.register_dataset(
            project_id=project_id,
            task_id=None,
            kind="cumulative_included",
            label="Cumulative included records",
            path=output_path,
            record_count=len(deduped),
            file_format="ris",
            source_dataset_ids=[item["id"] for item in datasets],
            metadata={"generated": True},
            dataset_id="cumulative-included",
        )

    def _project_root(self, project_id: str) -> Path:
        return self.projects_dir / project_id

    @staticmethod
    def _read(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
