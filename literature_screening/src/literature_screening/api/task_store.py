from __future__ import annotations

import json
import threading
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


@dataclass(slots=True)
class StoredTask:
    task_id: str
    root_dir: Path
    payload: dict[str, Any]


class TaskStore:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.tasks_dir = root_dir / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def create_task(self, *, kind: str, title: str, metadata: dict[str, Any] | None = None) -> StoredTask:
        task_id = uuid.uuid4().hex[:12]
        root_dir = self.tasks_dir / task_id
        root_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now().astimezone().isoformat()
        payload = {
            "id": task_id,
            "kind": kind,
            "status": "pending",
            "title": title,
            "phase": "queued",
            "phase_label": "Queued",
            "progress_current": 0,
            "progress_total": None,
            "progress_message": None,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {},
            "summary": None,
            "error": None,
            "artifacts": {},
            "run_root": None,
            "output_dir": None,
            "markdown_preview": None,
            "records": [],
        }
        self._write(root_dir / "task.json", payload)
        return StoredTask(task_id=task_id, root_dir=root_dir, payload=payload)

    def load_task(self, task_id: str) -> dict[str, Any]:
        return self._read(self.tasks_dir / task_id / "task.json")

    def list_tasks(self) -> list[dict[str, Any]]:
        tasks = []
        for path in sorted(self.tasks_dir.glob("*/task.json"), reverse=True):
            tasks.append(self._read(path))
        tasks.sort(key=lambda item: item["created_at"], reverse=True)
        return tasks

    def update(self, task_id: str, **changes: Any) -> dict[str, Any]:
        task_path = self.tasks_dir / task_id / "task.json"
        with self._lock:
            payload = self._read(task_path)
            payload.update(changes)
            payload["updated_at"] = datetime.now().astimezone().isoformat()
            self._write(task_path, payload)
        return payload

    def run_in_background(
        self,
        task: StoredTask,
        worker: Callable[[StoredTask], dict[str, Any]],
    ) -> None:
        thread = threading.Thread(target=self._run_worker, args=(task, worker), daemon=True)
        thread.start()

    def _run_worker(self, task: StoredTask, worker: Callable[[StoredTask], dict[str, Any]]) -> None:
        self.update(
            task.task_id,
            status="running",
            phase="starting",
            phase_label="Starting",
            progress_current=0,
            progress_total=None,
            progress_message="Initializing task",
        )
        try:
            result = worker(task)
            self.update(
                task.task_id,
                status="succeeded",
                phase="completed",
                phase_label="Completed",
                progress_message="Task completed",
                **result,
            )
        except Exception as exc:
            detail = "".join(traceback.format_exception(exc))
            self.update(
                task.task_id,
                status="failed",
                phase="failed",
                phase_label="Failed",
                progress_message=str(exc),
                error=detail,
            )

    @staticmethod
    def _read(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _write(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

