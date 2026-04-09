from __future__ import annotations

import json
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


def test_task_store_persists_paths_relatively_and_hydrates_on_load(tmp_path: Path) -> None:
    store = TaskStore(tmp_path / "api_runs")
    task = store.create_task(kind="screening", title="demo")

    run_root = store.tasks_dir / task.task_id / "screening_run"
    output_dir = run_root / "screening_output"
    upload_path = store.tasks_dir / task.task_id / "uploads" / "input.ris"
    artifact_path = output_dir / "run_summary.json"
    virtual_dataset_path = store.root_dir / "projects" / "project-1" / "derived" / "fulltext_ready.ris"

    store.update(
        task.task_id,
        run_root=str(run_root),
        output_dir=str(output_dir),
        artifacts={
            "run_summary": {
                "path": str(artifact_path),
                "filename": artifact_path.name,
            }
        },
        metadata={
            "uploaded_input_paths": [str(upload_path)],
            "virtual_dataset_paths": [str(virtual_dataset_path)],
        },
    )

    raw_payload = json.loads((store.tasks_dir / task.task_id / "task.json").read_text(encoding="utf-8"))
    assert raw_payload["run_root"] == f"tasks/{task.task_id}/screening_run"
    assert raw_payload["output_dir"] == f"tasks/{task.task_id}/screening_run/screening_output"
    assert raw_payload["artifacts"]["run_summary"]["path"] == f"tasks/{task.task_id}/screening_run/screening_output/run_summary.json"
    assert raw_payload["metadata"]["uploaded_input_paths"] == [f"tasks/{task.task_id}/uploads/input.ris"]
    assert raw_payload["metadata"]["virtual_dataset_paths"] == ["projects/project-1/derived/fulltext_ready.ris"]

    payload = store.load_task(task.task_id)
    assert payload["run_root"] == str(run_root)
    assert payload["output_dir"] == str(output_dir)
    assert payload["artifacts"]["run_summary"]["path"] == str(artifact_path)
    assert payload["metadata"]["uploaded_input_paths"] == [str(upload_path)]
    assert payload["metadata"]["virtual_dataset_paths"] == [str(virtual_dataset_path)]
