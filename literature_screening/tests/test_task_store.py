from __future__ import annotations

import time
from pathlib import Path

from literature_screening.api.task_store import StoredTask, TaskStore


def _wait_for_status(store: TaskStore, task_id: str, expected: str, timeout: float = 3.0) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        payload = store.load_task(task_id)
        if payload["status"] == expected:
            return payload
        time.sleep(0.05)
    raise AssertionError(f"Task {task_id} did not reach status {expected!r} within {timeout} seconds")


def test_task_store_records_events(tmp_path: Path) -> None:
    store = TaskStore(tmp_path)
    task = store.create_task(kind="screening", title="demo")

    events = store.load_events(task.task_id)
    assert len(events) == 1
    assert events[0]["kind"] == "task-created"


def test_task_store_retry_updates_attempt_count(tmp_path: Path) -> None:
    store = TaskStore(tmp_path)
    task = store.create_task(kind="screening", title="demo")

    def worker(stored_task: StoredTask) -> dict:
        return {"summary": {"ok": True}}

    store.run_in_background(task, worker)
    payload = _wait_for_status(store, task.task_id, "succeeded")
    assert payload["attempt_count"] == 1

    store.retry_in_background(task.task_id, worker)
    payload = _wait_for_status(store, task.task_id, "succeeded")
    assert payload["attempt_count"] == 2

    events = store.load_events(task.task_id)
    assert any(item["kind"] == "task-retry" for item in events)
