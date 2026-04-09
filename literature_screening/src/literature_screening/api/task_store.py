from __future__ import annotations

import json
import shutil
import threading
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from literature_screening.storage_paths import rewrite_storage_payload


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
            "cancel_requested": False,
            "title": title,
            "phase": "queued",
            "phase_label": "Queued",
            "progress_current": 0,
            "progress_total": None,
            "progress_message": None,
            "created_at": now,
            "updated_at": now,
            "attempt_count": 0,
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
        self.append_event(task_id, kind="task-created", message=f"Created {kind} task", metadata={"title": title})
        return StoredTask(task_id=task_id, root_dir=root_dir, payload=payload)

    def load_task(self, task_id: str) -> dict[str, Any]:
        return self._read(self.tasks_dir / task_id / "task.json")

    def delete_task(self, task_id: str) -> None:
        task_root = self.tasks_dir / task_id
        if task_root.exists():
            shutil.rmtree(task_root)

    def list_tasks(self) -> list[dict[str, Any]]:
        tasks = []
        for path in sorted(self.tasks_dir.glob("*/task.json"), reverse=True):
            tasks.append(self._read(path))
        tasks.sort(key=lambda item: item["created_at"], reverse=True)
        return tasks

    def load_events(self, task_id: str) -> list[dict[str, Any]]:
        events_path = self.tasks_dir / task_id / "events.json"
        if not events_path.exists():
            return []
        return self._read(events_path)

    def update(self, task_id: str, **changes: Any) -> dict[str, Any]:
        task_path = self.tasks_dir / task_id / "task.json"
        with self._lock:
            payload = self._read(task_path)
            payload.update(changes)
            payload["updated_at"] = datetime.now().astimezone().isoformat()
            self._write(task_path, payload)
        return payload

    def append_event(
        self,
        task_id: str,
        *,
        kind: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        events_path = self.tasks_dir / task_id / "events.json"
        with self._lock:
            if events_path.exists():
                events = json.loads(events_path.read_text(encoding="utf-8"))
            else:
                events = []
            event = {
                "id": uuid.uuid4().hex[:12],
                "kind": kind,
                "message": message,
                "metadata": metadata or {},
                "created_at": datetime.now().astimezone().isoformat(),
            }
            events.append(event)
            self._write(events_path, events)
        return event

    def run_in_background(
        self,
        task: StoredTask,
        worker: Callable[[StoredTask], dict[str, Any]],
    ) -> None:
        thread = threading.Thread(target=self._run_worker, args=(task, worker), daemon=True)
        thread.start()

    def retry_in_background(
        self,
        task_id: str,
        worker: Callable[[StoredTask], dict[str, Any]],
    ) -> dict[str, Any]:
        payload = self.load_task(task_id)
        next_attempt = int(payload.get("attempt_count", 0)) + 1
        payload = self.update(
            task_id,
            status="pending",
            cancel_requested=False,
            phase="queued",
            phase_label="Queued",
            progress_current=0,
            progress_total=None,
            progress_message="Retry scheduled",
            error=None,
            attempt_count=next_attempt,
        )
        self.append_event(task_id, kind="task-retry", message="Retry scheduled", metadata={"attempt_count": next_attempt})
        stored = StoredTask(task_id=task_id, root_dir=self.tasks_dir / task_id, payload=payload)
        self.run_in_background(stored, worker)
        return payload

    def cancel_task(self, task_id: str) -> dict[str, Any]:
        payload = self.update(
            task_id,
            cancel_requested=True,
            status="cancelled",
            phase="cancelled",
            phase_label="Cancelled",
            progress_message="Cancellation requested. The current request may still finish in background.",
        )
        self.append_event(task_id, kind="task-cancel-requested", message="Cancellation requested")
        return payload

    def is_cancel_requested(self, task_id: str) -> bool:
        payload = self.load_task(task_id)
        return bool(payload.get("cancel_requested"))

    def _run_worker(self, task: StoredTask, worker: Callable[[StoredTask], dict[str, Any]]) -> None:
        current = self.load_task(task.task_id)
        attempt_count = int(current.get("attempt_count", 0)) or 1
        if current.get("cancel_requested"):
            self.update(
                task.task_id,
                status="cancelled",
                phase="cancelled",
                phase_label="Cancelled",
                progress_message="Task cancelled before execution started",
            )
            self.append_event(task.task_id, kind="task-cancelled", message="Task cancelled before execution started")
            return
        self.append_event(task.task_id, kind="task-started", message="Task execution started", metadata={"attempt_count": attempt_count})
        self.update(
            task.task_id,
            status="running",
            phase="starting",
            phase_label="Starting",
            progress_current=0,
            progress_total=None,
            progress_message="Initializing task",
            attempt_count=attempt_count,
        )
        try:
            result = worker(task)
            latest = self.load_task(task.task_id)
            if latest.get("cancel_requested") or latest.get("status") == "cancelled":
                self.append_event(
                    task.task_id,
                    kind="task-cancelled",
                    message="Task result discarded because cancellation was requested",
                )
                return
            self.update(
                task.task_id,
                status="succeeded",
                phase="completed",
                phase_label="Completed",
                progress_message="Task completed",
                **result,
            )
            self.append_event(task.task_id, kind="task-succeeded", message="Task completed successfully")
        except Exception as exc:
            latest = self.load_task(task.task_id)
            if latest.get("cancel_requested") or latest.get("status") == "cancelled":
                self.update(
                    task.task_id,
                    status="cancelled",
                    phase="cancelled",
                    phase_label="Cancelled",
                    progress_message="Task cancelled by user",
                    error=None,
                )
                self.append_event(task.task_id, kind="task-cancelled", message="Task cancelled by user")
                return
            if exc.__class__.__name__ == "TaskCancelledError":
                self.update(
                    task.task_id,
                    status="cancelled",
                    phase="cancelled",
                    phase_label="Cancelled",
                    progress_message=str(exc),
                    error=None,
                )
                self.append_event(task.task_id, kind="task-cancelled", message=str(exc))
                return
            detail = "".join(traceback.format_exception(exc))
            self.update(
                task.task_id,
                status="failed",
                phase="failed",
                phase_label="Failed",
                progress_message=str(exc),
                error=detail,
            )
            self.append_event(task.task_id, kind="task-failed", message=str(exc), metadata={"error_type": exc.__class__.__name__})

    def _read(self, path: Path) -> Any:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return rewrite_storage_payload(payload, storage_root=self.root_dir, mode="hydrate")

    def _write(self, path: Path, payload: Any) -> None:
        serialized = rewrite_storage_payload(payload, storage_root=self.root_dir, mode="dehydrate")
        path.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")
