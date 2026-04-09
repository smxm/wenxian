from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from literature_screening.api import app as app_module
from literature_screening.api.app import app
from literature_screening.api.task_store import TaskStore
from literature_screening.api.workspace_store import WorkspaceStore
from literature_screening.core.config import load_run_config


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_meta_endpoint() -> None:
    response = client.get("/api/meta")
    assert response.status_code == 200
    payload = response.json()
    assert {item["provider"] for item in payload["providers"]} == {"deepseek", "kimi"}
    assert ".ris" in payload["acceptedInputFormats"]
    assert payload["strategyDefaults"]["model_name"] == "deepseek-reasoner"
    assert {item["value"] for item in payload["strategyDefaults"]["databases"]} == {"scopus", "wos", "pubmed", "cnki"}


def test_project_create_and_list() -> None:
    created = client.post(
        "/api/projects",
        json={"name": "api-test-project", "topic": "api topic", "description": "desc"},
    )
    assert created.status_code == 200
    project = created.json()
    assert project["name"] == "api-test-project"

    listing = client.get("/api/projects")
    assert listing.status_code == 200
    assert any(item["id"] == project["id"] for item in listing.json())


def test_review_override_is_cumulative(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    task = task_store.create_task(kind="screening", title="review-test")
    output_dir = tmp_path / "screening_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = [
        {
            "paper_id": "paper_1",
            "title": "Paper One",
            "decision": "include",
            "reason": "initial include",
            "year": 2024,
            "journal": "Journal A",
            "abstract": "Abstract A",
        },
        {
            "paper_id": "paper_2",
            "title": "Paper Two",
            "decision": "include",
            "reason": "initial include",
            "year": 2024,
            "journal": "Journal B",
            "abstract": "Abstract B",
        },
    ]
    decisions = [
        {"paper_id": "paper_1", "decision": "include", "reason": "initial include"},
        {"paper_id": "paper_2", "decision": "include", "reason": "initial include"},
    ]
    deduped_records = [
        {
            "paper_id": "paper_1",
            "entry_type": "article",
            "title": "Paper One",
            "authors": ["Author A"],
            "year": 2024,
            "journal": "Journal A",
            "doi": None,
            "abstract": "Abstract A",
            "keywords": [],
            "normalized_title": None,
            "raw_bibtex": None,
            "source_files": [],
            "source_keys": [],
            "merged_from": [],
            "status": "unprocessed",
        },
        {
            "paper_id": "paper_2",
            "entry_type": "article",
            "title": "Paper Two",
            "authors": ["Author B"],
            "year": 2024,
            "journal": "Journal B",
            "doi": None,
            "abstract": "Abstract B",
            "keywords": [],
            "normalized_title": None,
            "raw_bibtex": None,
            "source_files": [],
            "source_keys": [],
            "merged_from": [],
            "status": "unprocessed",
        },
    ]
    (output_dir / "screening_decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "deduped_records.json").write_text(json.dumps(deduped_records, ensure_ascii=False, indent=2), encoding="utf-8")
    task_store.update(
        task.task_id,
        status="succeeded",
        phase="completed",
        phase_label="Completed",
        output_dir=str(output_dir),
        records=rows,
        summary={"included_count": 2, "excluded_count": 0, "uncertain_count": 0, "processed_count": 2},
    )

    response_one = client.post(
        f"/api/tasks/{task.task_id}/review-overrides",
        json={"paper_id": "paper_1", "decision": "exclude", "reason": "remove one"},
    )
    assert response_one.status_code == 200
    assert response_one.json()["summary"]["included_count"] == 1
    assert response_one.json()["summary"]["excluded_count"] == 1

    response_two = client.post(
        f"/api/tasks/{task.task_id}/review-overrides",
        json={"paper_id": "paper_2", "decision": "exclude", "reason": "remove two"},
    )
    assert response_two.status_code == 200
    payload = response_two.json()
    assert payload["summary"]["included_count"] == 0
    assert payload["summary"]["excluded_count"] == 2
    reviewed_map = {item["paper_id"]: item["decision"] for item in payload["records"]}
    assert reviewed_map == {"paper_1": "exclude", "paper_2": "exclude"}


def test_bulk_review_override_matches_reference_list(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    task = task_store.create_task(kind="screening", title="bulk-review-test")
    output_dir = tmp_path / "screening_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = [
        {
            "paper_id": "paper_1",
            "title": "Paper One",
            "decision": "include",
            "reason": "initial include",
            "year": 2024,
            "journal": "Journal A",
            "abstract": "Abstract A",
        },
        {
            "paper_id": "paper_2",
            "title": "Paper Two",
            "decision": "include",
            "reason": "initial include",
            "year": 2024,
            "journal": "Journal B",
            "abstract": "Abstract B",
        },
        {
            "paper_id": "paper_3",
            "title": "Paper Three",
            "decision": "exclude",
            "reason": "initial exclude",
            "year": 2024,
            "journal": "Journal C",
            "abstract": "Abstract C",
        },
    ]
    decisions = [
        {"paper_id": "paper_1", "decision": "include", "reason": "initial include"},
        {"paper_id": "paper_2", "decision": "include", "reason": "initial include"},
        {"paper_id": "paper_3", "decision": "exclude", "reason": "initial exclude"},
    ]
    deduped_records = [
        {
            "paper_id": "paper_1",
            "entry_type": "article",
            "title": "Paper One",
            "authors": ["Author A"],
            "year": 2024,
            "journal": "Journal A",
            "doi": None,
            "abstract": "Abstract A",
            "keywords": [],
            "normalized_title": None,
            "raw_bibtex": None,
            "source_files": [],
            "source_keys": [],
            "merged_from": [],
            "status": "unprocessed",
        },
        {
            "paper_id": "paper_2",
            "entry_type": "article",
            "title": "Paper Two",
            "authors": ["Author B"],
            "year": 2024,
            "journal": "Journal B",
            "doi": None,
            "abstract": "Abstract B",
            "keywords": [],
            "normalized_title": None,
            "raw_bibtex": None,
            "source_files": [],
            "source_keys": [],
            "merged_from": [],
            "status": "unprocessed",
        },
        {
            "paper_id": "paper_3",
            "entry_type": "article",
            "title": "Paper Three",
            "authors": ["Author C"],
            "year": 2024,
            "journal": "Journal C",
            "doi": None,
            "abstract": "Abstract C",
            "keywords": [],
            "normalized_title": None,
            "raw_bibtex": None,
            "source_files": [],
            "source_keys": [],
            "merged_from": [],
            "status": "unprocessed",
        },
    ]
    (output_dir / "screening_decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "deduped_records.json").write_text(json.dumps(deduped_records, ensure_ascii=False, indent=2), encoding="utf-8")
    task_store.update(
        task.task_id,
        status="succeeded",
        phase="completed",
        phase_label="Completed",
        output_dir=str(output_dir),
        records=rows,
        summary={"included_count": 2, "excluded_count": 1, "uncertain_count": 0, "processed_count": 3},
    )

    response = client.post(
        f"/api/tasks/{task.task_id}/review-overrides/bulk",
        json={
            "entries_text": "[1] Author A. Paper One[J]. Journal A, 2024.\n[2] Author B. Paper Two[J]. Journal B, 2024.",
            "decision": "exclude",
            "reason": "bulk remove",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["included_count"] == 0
    assert payload["summary"]["excluded_count"] == 3
    reviewed_map = {item["paper_id"]: item["decision"] for item in payload["records"]}
    assert reviewed_map == {"paper_1": "exclude", "paper_2": "exclude", "paper_3": "exclude"}


def test_fulltext_queue_rebuild_and_status_update(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="fulltext-project", topic="topic", description="")
    ris_path = tmp_path / "included.ris"
    ris_path.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Paper One",
                "JO  - Journal A",
                "PY  - 2024",
                "DO  - 10.1000/paper-one",
                "ER  - ",
                "TY  - JOUR",
                "TI  - Paper Two",
                "JO  - Journal B",
                "PY  - 2025",
                "DO  - 10.1000/paper-two",
                "ER  - ",
            ]
        ),
        encoding="utf-8",
    )
    dataset = workspace_store.register_dataset(
        project_id=project["id"],
        task_id=None,
        kind="included_reviewed",
        label="Reviewed included records",
        path=ris_path,
        record_count=2,
        file_format="ris",
    )

    rebuild = client.post(
        f"/api/projects/{project['id']}/fulltext/rebuild",
        json={"source_dataset_ids": [dataset["id"]]},
    )
    assert rebuild.status_code == 200
    payload = rebuild.json()
    assert payload["fulltext_source_dataset_ids"] == [dataset["id"]]
    assert len(payload["fulltext_queue"]) == 2
    assert {item["status"] for item in payload["fulltext_queue"]} == {"pending"}

    update = client.post(
        f"/api/projects/{project['id']}/fulltext/status",
        json={"paper_id": payload["fulltext_queue"][0]["paper_id"], "status": "ready", "note": "downloaded"},
    )
    assert update.status_code == 200
    updated_payload = update.json()
    ready_item = next(item for item in updated_payload["fulltext_queue"] if item["status"] == "ready")
    assert ready_item["note"] == "downloaded"
    ready_dataset = next(item for item in updated_payload["datasets"] if item["kind"] == "fulltext_ready")
    assert ready_dataset["record_count"] == 1


def test_workspace_store_persists_dataset_paths_relatively(tmp_path: Path) -> None:
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    project = workspace_store.create_project(name="relative-path-project", topic="topic", description="")
    derived_dir = workspace_store.root_dir / "projects" / project["id"] / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = derived_dir / "included.ris"
    dataset_path.write_text("TY  - JOUR\nTI  - Demo Paper\nER  - \n", encoding="utf-8")

    dataset = workspace_store.register_dataset(
        project_id=project["id"],
        task_id=None,
        kind="included_reviewed",
        label="Reviewed included records",
        path=dataset_path,
        record_count=1,
        file_format="ris",
    )

    raw_payload = json.loads(
        (workspace_store.root_dir / "projects" / project["id"] / "datasets" / f"{dataset['id']}.json").read_text(encoding="utf-8")
    )
    assert raw_payload["path"] == f"projects/{project['id']}/derived/included.ris"

    loaded = workspace_store.load_dataset(project["id"], dataset["id"])
    assert loaded["path"] == str(dataset_path)


def test_dataset_api_returns_absolute_and_relative_paths(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="relative-path-project", topic="topic", description="")
    derived_dir = workspace_store.root_dir / "projects" / project["id"] / "derived"
    derived_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = derived_dir / "included.ris"
    dataset_path.write_text("TY  - JOUR\nTI  - Demo Paper\nER  - \n", encoding="utf-8")
    dataset = workspace_store.register_dataset(
        project_id=project["id"],
        task_id=None,
        kind="included_reviewed",
        label="Reviewed included records",
        path=dataset_path,
        record_count=1,
        file_format="ris",
    )

    response = client.get(f"/api/datasets/{dataset['id']}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["path"] == str(dataset_path)
    assert payload["relative_path"] == f"projects/{project['id']}/derived/included.ris"

    project_response = client.get(f"/api/projects/{project['id']}")
    assert project_response.status_code == 200
    project_payload = project_response.json()
    dataset_payload = next(item for item in project_payload["datasets"] if item["id"] == dataset["id"])
    assert dataset_payload["path"] == str(dataset_path)
    assert dataset_payload["relative_path"] == f"projects/{project['id']}/derived/included.ris"


def test_task_detail_api_returns_absolute_and_relative_task_paths(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    task = task_store.create_task(kind="screening", title="relative-task-paths")
    run_root = task_store.tasks_dir / task.task_id / "screening_run"
    output_dir = run_root / "screening_output"
    task_store.update(
        task.task_id,
        status="succeeded",
        phase="completed",
        phase_label="Completed",
        run_root=str(run_root),
        output_dir=str(output_dir),
    )

    response = client.get(f"/api/tasks/{task.task_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["run_root"] == str(run_root)
    assert payload["run_root_relative"] == f"tasks/{task.task_id}/screening_run"
    assert payload["output_dir"] == str(output_dir)
    assert payload["output_dir_relative"] == f"tasks/{task.task_id}/screening_run/screening_output"


def test_load_run_config_resolves_api_runs_relative_paths_from_storage_root(tmp_path: Path) -> None:
    api_runs_root = tmp_path / "api_runs"
    run_root = api_runs_root / "tasks" / "task-1" / "screening_run"
    config_path = run_root / "generated_screening_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "\n".join(
            [
                "project:",
                "  name: demo",
                "  output_dir: tasks/task-1/screening_run/screening_output",
                "input:",
                "  input_files:",
                "    - tasks/task-1/screening_run/inputs/demo.ris",
                "dedup:",
                "  enabled: true",
                "screening:",
                "  batch_size: 1",
                "  target_include_count: 10",
                "  stop_when_target_reached: false",
                "  allow_uncertain: true",
                "  retry_times: 1",
                "  request_timeout_seconds: 60",
                "criteria:",
                "  topic: demo",
                "  inclusion:",
                "    - keep",
                "  exclusion:",
                "    - drop",
                "model:",
                "  provider: deepseek",
                "  model_name: deepseek-chat",
                "  api_base_url: https://api.deepseek.com/v1",
                "  api_key_env: DEEPSEEK_API_KEY",
                "  temperature: 0",
                "  max_tokens: 256",
                "  min_request_interval_seconds: 1",
                "report:",
                "  export_included_ris: true",
                "  export_excluded_ris: false",
                "  export_unused_ris: true",
                "  export_included_bib: false",
                "  export_excluded_bib: false",
                "  export_unused_bib: false",
                "  included_report_format: md",
                "  excluded_report_format: md",
                "  summary_format: json",
            ]
        ),
        encoding="utf-8",
    )

    config = load_run_config(config_path)
    expected_output_dir = (api_runs_root / "tasks" / "task-1" / "screening_run" / "screening_output").resolve()
    expected_input_path = (api_runs_root / "tasks" / "task-1" / "screening_run" / "inputs" / "demo.ris").resolve()
    assert config.project.output_dir == str(expected_output_dir)
    assert config.input.input_files == [str(expected_input_path)]


def test_fulltext_queue_rebuild_uses_project_scoped_cumulative_dataset(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    other_project = workspace_store.create_project(name="other-project", topic="topic", description="")
    other_ris_path = tmp_path / "other-included.ris"
    other_ris_path.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Other Project Paper",
                "JO  - Journal A",
                "PY  - 2024",
                "DO  - 10.1000/other-paper",
                "ER  - ",
            ]
        ),
        encoding="utf-8",
    )
    other_dataset = workspace_store.register_dataset(
        project_id=other_project["id"],
        task_id=None,
        kind="included_reviewed",
        label="Reviewed included records",
        path=other_ris_path,
        record_count=1,
        file_format="ris",
    )
    workspace_store.rebuild_cumulative_included_dataset(other_project["id"])

    project = workspace_store.create_project(name="fulltext-project", topic="topic", description="")
    ris_path = tmp_path / "included.ris"
    ris_path.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Current Project Paper",
                "JO  - Journal B",
                "PY  - 2025",
                "DO  - 10.1000/current-paper",
                "ER  - ",
            ]
        ),
        encoding="utf-8",
    )
    dataset = workspace_store.register_dataset(
        project_id=project["id"],
        task_id=None,
        kind="included_reviewed",
        label="Reviewed included records",
        path=ris_path,
        record_count=1,
        file_format="ris",
    )
    cumulative_dataset = workspace_store.rebuild_cumulative_included_dataset(project["id"])
    assert cumulative_dataset is not None
    assert cumulative_dataset["id"] == "cumulative-included"
    assert other_dataset["id"] != dataset["id"]

    rebuild = client.post(
        f"/api/projects/{project['id']}/fulltext/rebuild",
        json={"source_dataset_ids": [cumulative_dataset["id"]]},
    )
    assert rebuild.status_code == 200
    payload = rebuild.json()
    assert payload["fulltext_source_dataset_ids"] == [cumulative_dataset["id"]]
    assert len(payload["fulltext_queue"]) == 1
    assert payload["fulltext_queue"][0]["title"] == "Current Project Paper"


def test_report_task_rejects_empty_fulltext_ready_source(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="report-project", topic="topic", description="")
    ris_path = tmp_path / "included.ris"
    ris_path.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Paper One",
                "JO  - Journal A",
                "PY  - 2024",
                "DO  - 10.1000/paper-one",
                "ER  - ",
            ]
        ),
        encoding="utf-8",
    )
    dataset = workspace_store.register_dataset(
        project_id=project["id"],
        task_id=None,
        kind="included_reviewed",
        label="Reviewed included records",
        path=ris_path,
        record_count=1,
        file_format="ris",
    )
    workspace_store.rebuild_fulltext_queue(project["id"], source_dataset_ids=[dataset["id"]])

    response = client.post(
        "/api/report/tasks",
        json={
            "title": "report",
            "screening_task_id": None,
            "dataset_ids": ["fulltext-ready"],
            "project_topic": "topic",
            "report_name": "simple_report",
            "retry_times": 1,
            "timeout_seconds": 30,
            "reference_style": "gbt7714",
            "model": {
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_base_url": "https://api.deepseek.com/v1",
                "api_key_env": "DEEPSEEK_API_KEY",
                "api_key": "",
                "temperature": 0,
                "max_tokens": 256,
                "min_request_interval_seconds": 1,
            },
        },
    )
    assert response.status_code == 400
    assert "Selected report source is empty" in response.json()["detail"]


def test_fulltext_queue_rebuild_clears_ready_dataset_when_source_file_disappears(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="fulltext-project", topic="topic", description="")
    ris_path = tmp_path / "included.ris"
    ris_path.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Paper One",
                "JO  - Journal A",
                "PY  - 2024",
                "DO  - 10.1000/paper-one",
                "ER  - ",
            ]
        ),
        encoding="utf-8",
    )
    dataset = workspace_store.register_dataset(
        project_id=project["id"],
        task_id=None,
        kind="included_reviewed",
        label="Reviewed included records",
        path=ris_path,
        record_count=1,
        file_format="ris",
    )

    rebuild = client.post(
        f"/api/projects/{project['id']}/fulltext/rebuild",
        json={"source_dataset_ids": [dataset["id"]]},
    )
    assert rebuild.status_code == 200
    queue_item = rebuild.json()["fulltext_queue"][0]

    update = client.post(
        f"/api/projects/{project['id']}/fulltext/status",
        json={"paper_id": queue_item["paper_id"], "status": "ready", "note": "downloaded"},
    )
    assert update.status_code == 200
    ready_dataset = next(item for item in update.json()["datasets"] if item["kind"] == "fulltext_ready")
    assert ready_dataset["record_count"] == 1

    ris_path.unlink()

    rebuild_after_missing_source = client.post(
        f"/api/projects/{project['id']}/fulltext/rebuild",
        json={"source_dataset_ids": [dataset["id"]]},
    )
    assert rebuild_after_missing_source.status_code == 200
    payload = rebuild_after_missing_source.json()
    assert payload["fulltext_queue"] == []
    ready_dataset = next(item for item in payload["datasets"] if item["kind"] == "fulltext_ready")
    assert ready_dataset["record_count"] == 0
    assert ready_dataset["source_dataset_ids"] == [dataset["id"]]


def test_report_task_rebuilds_fulltext_ready_from_its_own_source_selection(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)
    monkeypatch.setattr(task_store, "run_in_background", lambda task, worker: None)

    project = workspace_store.create_project(name="report-project", topic="topic", description="")
    source_a = tmp_path / "included_a.ris"
    source_a.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Paper One",
                "JO  - Journal A",
                "PY  - 2024",
                "DO  - 10.1000/paper-one",
                "ER  - ",
            ]
        ),
        encoding="utf-8",
    )
    source_b = tmp_path / "included_b.ris"
    source_b.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Paper Two",
                "JO  - Journal B",
                "PY  - 2025",
                "DO  - 10.1000/paper-two",
                "ER  - ",
            ]
        ),
        encoding="utf-8",
    )
    dataset_a = workspace_store.register_dataset(
        project_id=project["id"],
        task_id=None,
        kind="included_reviewed",
        label="Reviewed included records A",
        path=source_a,
        record_count=1,
        file_format="ris",
    )
    dataset_b = workspace_store.register_dataset(
        project_id=project["id"],
        task_id=None,
        kind="included_reviewed",
        label="Reviewed included records B",
        path=source_b,
        record_count=1,
        file_format="ris",
    )

    rebuild = client.post(
        f"/api/projects/{project['id']}/fulltext/rebuild",
        json={"source_dataset_ids": [dataset_a["id"]]},
    )
    assert rebuild.status_code == 200
    queue_item = rebuild.json()["fulltext_queue"][0]

    update = client.post(
        f"/api/projects/{project['id']}/fulltext/status",
        json={"paper_id": queue_item["paper_id"], "status": "ready", "note": "downloaded"},
    )
    assert update.status_code == 200

    other_project = workspace_store.create_project(name="other-project", topic="other", description="")
    other_ready_path = tmp_path / "other_fulltext_ready.ris"
    other_ready_path.write_text("", encoding="utf-8")
    workspace_store.register_dataset(
        project_id=other_project["id"],
        task_id=None,
        kind="fulltext_ready",
        label="Fulltext ready records",
        path=other_ready_path,
        record_count=0,
        file_format="ris",
        dataset_id="fulltext-ready",
    )

    original_find_dataset = workspace_store.find_dataset

    def _find_dataset_preferring_other(dataset_id: str):
        if dataset_id == "fulltext-ready":
            return workspace_store.load_dataset(other_project["id"], dataset_id)
        return original_find_dataset(dataset_id)

    monkeypatch.setattr(workspace_store, "find_dataset", _find_dataset_preferring_other)

    response = client.post(
        "/api/report/tasks",
        json={
            "title": "report",
            "project_id": project["id"],
            "screening_task_id": None,
            "dataset_ids": ["fulltext-ready"],
            "project_topic": "topic",
            "report_name": "simple_report",
            "retry_times": 1,
            "timeout_seconds": 30,
            "reference_style": "gbt7714",
            "model": {
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_base_url": "https://api.deepseek.com/v1",
                "api_key_env": "DEEPSEEK_API_KEY",
                "api_key": "",
                "temperature": 0,
                "max_tokens": 256,
                "min_request_interval_seconds": 1,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["input_dataset_ids"] == ["fulltext-ready"]

    ready_dataset = workspace_store.load_dataset(project["id"], "fulltext-ready")
    assert ready_dataset["record_count"] == 1
    assert ready_dataset["source_dataset_ids"] == [dataset_a["id"]]
    assert ready_dataset["source_dataset_ids"] != [dataset_b["id"]]
