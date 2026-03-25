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
        all_datasets = [
            item
            for item in self.list_project_datasets(project_id)
            if item["kind"] in {"included", "included_reviewed"}
        ]
        chosen_by_task: dict[str, dict[str, Any]] = {}
        fallback_datasets: list[dict[str, Any]] = []

        for item in sorted(all_datasets, key=lambda entry: entry["created_at"]):
            task_id = item.get("task_id")
            if not task_id:
                fallback_datasets.append(item)
                continue
            current = chosen_by_task.get(task_id)
            if current is None:
                chosen_by_task[task_id] = item
                continue
            if current["kind"] == "included_reviewed":
                if item["kind"] == "included_reviewed":
                    chosen_by_task[task_id] = item
                continue
            if item["kind"] == "included_reviewed" or item["created_at"] >= current["created_at"]:
                chosen_by_task[task_id] = item

        datasets = [*chosen_by_task.values(), *fallback_datasets]
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

    def load_fulltext_queue(self, project_id: str) -> dict[str, Any]:
        path = self._project_root(project_id) / "derived" / "fulltext_queue.json"
        if not path.exists():
            return {"source_dataset_ids": [], "items": []}
        return self._read(path)

    def load_fulltext_statuses(self, project_id: str) -> dict[str, Any]:
        path = self._project_root(project_id) / "derived" / "fulltext_statuses.json"
        if not path.exists():
            return {}
        return self._read(path)

    def save_fulltext_statuses(self, project_id: str, payload: dict[str, Any]) -> None:
        path = self._project_root(project_id) / "derived" / "fulltext_statuses.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write(path, payload)

    def update_fulltext_status(
        self,
        *,
        project_id: str,
        paper_id: str,
        status: str,
        note: str = "",
        landing_url: str | None = None,
        pdf_url: str | None = None,
        oa_status: str | None = None,
    ) -> dict[str, Any]:
        statuses = self.load_fulltext_statuses(project_id)
        current = statuses.get(paper_id, {})
        current["status"] = status
        current["note"] = note
        if landing_url is not None:
            current["landing_url"] = landing_url
        if pdf_url is not None:
            current["pdf_url"] = pdf_url
        if oa_status is not None:
            current["oa_status"] = oa_status
        current["updated_at"] = datetime.now().astimezone().isoformat()
        statuses[paper_id] = current
        self.save_fulltext_statuses(project_id, statuses)
        return current

    def rebuild_fulltext_queue(
        self,
        project_id: str,
        *,
        source_dataset_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        datasets = self.list_project_datasets(project_id)
        if source_dataset_ids:
            selected = [item for item in datasets if item["id"] in source_dataset_ids]
        else:
            selected = [item for item in datasets if item["kind"] == "cumulative_included"]
            if not selected:
                selected = [item for item in datasets if item["kind"] in {"included_reviewed", "included"}]
                selected.sort(key=lambda item: item["created_at"])
                if selected:
                    selected = [selected[-1]]

        derived_dir = self._project_root(project_id) / "derived"
        derived_dir.mkdir(parents=True, exist_ok=True)
        queue_path = derived_dir / "fulltext_queue.json"
        ready_path = derived_dir / "fulltext_ready.ris"
        selected_ids = [item["id"] for item in selected]
        paths = [Path(item["path"]) for item in selected if Path(item["path"]).exists()]
        if not paths:
            payload = {"source_dataset_ids": selected_ids, "items": []}
            self._write(queue_path, payload)
            export_ris([], ready_path)
            self.register_dataset(
                project_id=project_id,
                task_id=None,
                kind="fulltext_ready",
                label="Fulltext ready records",
                path=ready_path,
                record_count=0,
                file_format="ris",
                source_dataset_ids=selected_ids,
                metadata={"generated": True, "status_counts": self._count_fulltext_statuses([])},
                dataset_id="fulltext-ready",
            )
            self.update_project(project_id)
            return payload

        records = deduplicate_records(parse_bibtex_files(paths, encoding="auto"))
        statuses = self.load_fulltext_statuses(project_id)
        items: list[dict[str, Any]] = []
        ready_records = []
        now = datetime.now().astimezone().isoformat()

        for record in records:
            state = statuses.get(record.paper_id, {})
            doi_url = f"https://doi.org/{record.doi}" if record.doi else None
            item = {
                "paper_id": record.paper_id,
                "title": record.title,
                "year": record.year,
                "journal": record.journal,
                "doi": record.doi,
                "doi_url": doi_url,
                "landing_url": state.get("landing_url") or doi_url,
                "pdf_url": state.get("pdf_url"),
                "oa_status": state.get("oa_status"),
                "status": state.get("status", "pending"),
                "note": state.get("note", ""),
                "updated_at": state.get("updated_at", now),
            }
            items.append(item)
            if item["status"] == "ready":
                ready_records.append(record)

        payload = {
            "source_dataset_ids": selected_ids,
            "items": items,
        }
        self._write(queue_path, payload)

        export_ris(ready_records, ready_path)
        self.register_dataset(
            project_id=project_id,
            task_id=None,
            kind="fulltext_ready",
            label="Fulltext ready records",
            path=ready_path,
            record_count=len(ready_records),
            file_format="ris",
            source_dataset_ids=selected_ids,
            metadata={"generated": True, "status_counts": self._count_fulltext_statuses(items)},
            dataset_id="fulltext-ready",
        )
        self.update_project(project_id)
        return payload

    @staticmethod
    def _count_fulltext_statuses(items: list[dict[str, Any]]) -> dict[str, int]:
        counts = {"pending": 0, "ready": 0, "unavailable": 0, "deferred": 0}
        for item in items:
            status = item.get("status", "pending")
            counts[status] = counts.get(status, 0) + 1
        return counts

    def _project_root(self, project_id: str) -> Path:
        return self.projects_dir / project_id

    @staticmethod
    def _read(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
