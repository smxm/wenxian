from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from literature_screening.api import app as app_module
from literature_screening.api.app import app
from literature_screening.api.task_store import TaskStore
from literature_screening.api.workspace_store import WorkspaceStore
from literature_screening.core.config import load_run_config
from literature_screening.core.models import PaperRecord


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


def test_thread_prefill_returns_strategy_plan_without_creating_thread(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    def fake_generate_strategy_job(request, progress_callback=None):
        output_dir = request.run_root_override / "strategy_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        plan_payload = {
            "topic": "混凝土结构工程研究",
            "intent_summary": "聚焦混凝土结构工程中的施工管理与质量控制证据。",
            "screening_topic": "混凝土结构工程施工管理研究",
            "inclusion": ["研究对象为混凝土结构工程项目", "涉及施工管理或质量控制"],
            "exclusion": ["纯材料机理论文", "与工程管理无关"],
            "search_blocks": [],
            "caution_notes": ["注意区分设计类与施工管理类研究。"],
        }
        (output_dir / "strategy_plan.json").write_text(json.dumps(plan_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (output_dir / "strategy_plan.md").write_text("# strategy", encoding="utf-8")
        (output_dir / "strategy_raw_response.txt").write_text("raw", encoding="utf-8")
        return SimpleNamespace(run_root=request.run_root_override, output_dir=output_dir, summary={}, markdown="# strategy", artifacts={})

    monkeypatch.setattr(app_module, "generate_strategy_job", fake_generate_strategy_job)

    response = client.post(
        "/api/threads/prefill",
        json={
            "research_need": "想研究混凝土结构工程中的施工管理与质量控制文献",
            "selected_databases": ["cnki", "wos"],
            "timeout_seconds": 120,
            "model": {
                "provider": "deepseek",
                "model_name": "deepseek-reasoner",
                "api_base_url": "https://api.deepseek.com/v1",
                "api_key_env": "DEEPSEEK_API_KEY",
                "api_key": "",
                "temperature": 0,
                "max_tokens": 4096,
                "min_request_interval_seconds": 2,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["strategy_plan"]["screening_topic"] == "混凝土结构工程施工管理研究"
    assert payload["strategy_plan"]["inclusion"] == ["研究对象为混凝土结构工程项目", "涉及施工管理或质量控制"]
    assert "混凝土结构工程施工管理研究" in payload["criteria_markdown"]
    assert workspace_store.list_projects() == []
    assert task_store.list_tasks() == []


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

    detail = client.get(f"/api/projects/{project['id']}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["thread_profile"]["screening"]["topic"] == "api topic"
    assert payload["thread_profile"]["strategy"]["selected_databases"] == ["scopus", "wos", "pubmed", "cnki"]


def test_project_workflow_update_persists_thread_defaults(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="workflow-project", topic="old topic", description="old desc")

    response = client.put(
        f"/api/projects/{project['id']}/workflow",
        json={
            "name": "workflow-project-renamed",
            "topic": "updated topic",
            "description": "updated desc",
            "thread_profile": {
                "strategy": {
                    "research_need": "find metabolomics screening studies",
                    "selected_databases": ["scopus", "pubmed"],
                    "model": {
                        "provider": "deepseek",
                        "model_name": "deepseek-reasoner",
                        "api_base_url": "https://api.deepseek.com/v1",
                        "api_key_env": "DEEPSEEK_API_KEY",
                        "api_key": None,
                        "temperature": 0,
                        "max_tokens": 4096,
                        "min_request_interval_seconds": 2,
                    },
                    "latest_task_id": None,
                    "plan": None,
                },
                "screening": {
                    "topic": "updated topic",
                    "criteria_markdown": "# 研究主题\n\nupdated topic\n\n# 纳入标准\n\n- human\n\n# 排除标准\n\n- review",
                    "inclusion": ["human"],
                    "exclusion": ["review"],
                    "model": {
                        "provider": "kimi",
                        "model_name": "moonshot-v1-auto",
                        "api_base_url": "https://api.moonshot.cn/v1",
                        "api_key_env": "KIMI_API_KEY",
                        "api_key": None,
                        "temperature": 0,
                        "max_tokens": 1536,
                        "min_request_interval_seconds": 2,
                    },
                    "batch_size": 12,
                    "target_include_count": None,
                    "stop_when_target_reached": False,
                    "allow_uncertain": True,
                    "retry_times": 6,
                    "request_timeout_seconds": 240,
                    "encoding": "auto",
                },
                "last_updated_at": None,
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "workflow-project-renamed"
    assert payload["topic"] == "updated topic"
    assert payload["thread_profile"]["strategy"]["research_need"] == "find metabolomics screening studies"
    assert payload["thread_profile"]["screening"]["batch_size"] == 12
    assert payload["thread_profile"]["screening"]["target_include_count"] is None


def test_strategy_task_updates_project_thread_profile(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    def run_immediately(task, worker):
        task_store._run_worker(task, worker)

    def fake_generate_strategy_job(request, progress_callback=None):
        run_root = task_store.tasks_dir / "strategy-task" / "strategy_run"
        output_dir = run_root / "strategy_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        plan_payload = {
            "topic": "脓毒症预后代谢组学研究",
            "intent_summary": "聚焦用于脓毒症预后判断的代谢组学研究与生物标志物证据。",
            "screening_topic": "脓毒症预后代谢组学相关研究",
            "inclusion": ["人群脓毒症队列研究", "涉及代谢组学标志物"],
            "exclusion": ["综述类文献", "动物实验研究"],
            "search_blocks": [
                {
                    "database": "pubmed",
                    "title": "PubMed 检索式",
                    "query": "sepsis AND metabolomics",
                    "lines": [],
                    "notes": ["使用英文检索式直接检索。"],
                }
            ],
            "caution_notes": ["注意区分死亡、重症和住院结局等不同预后定义。"],
        }
        (output_dir / "strategy_plan.json").write_text(json.dumps(plan_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (output_dir / "strategy_plan.md").write_text("# strategy", encoding="utf-8")
        (output_dir / "strategy_raw_response.txt").write_text("raw", encoding="utf-8")
        return SimpleNamespace(
            run_root=run_root,
            output_dir=output_dir,
            summary={
                "topic": plan_payload["topic"],
                "screening_topic": plan_payload["screening_topic"],
                "selected_databases": ["pubmed"],
                "database_count": 1,
                "inclusion_count": 2,
                "exclusion_count": 2,
            },
            markdown="# strategy",
            artifacts={
                "strategy_plan": output_dir / "strategy_plan.md",
                "strategy_plan_json": output_dir / "strategy_plan.json",
                "strategy_raw_response": output_dir / "strategy_raw_response.txt",
            },
        )

    monkeypatch.setattr(app_module.TASK_STORE, "run_in_background", run_immediately)
    monkeypatch.setattr(app_module, "generate_strategy_job", fake_generate_strategy_job)

    response = client.post(
        "/api/strategy/tasks",
        json={
            "title": "new-thread-kickoff",
            "project_id": None,
            "new_project_name": "Sepsis Thread",
            "new_project_description": "",
            "project_topic": "",
            "research_need": "Find metabolomics studies for sepsis prognosis and generate screening criteria.",
            "selected_databases": ["pubmed"],
            "model": {
                "provider": "deepseek",
                "model_name": "deepseek-reasoner",
                "api_base_url": "https://api.deepseek.com/v1",
                "api_key_env": "DEEPSEEK_API_KEY",
                "api_key": "",
                "temperature": 0,
                "max_tokens": 4096,
                "min_request_interval_seconds": 2,
            },
            "retry_times": 2,
            "timeout_seconds": 60,
        },
    )
    assert response.status_code == 200
    task_payload = response.json()
    project_id = task_payload["project_id"]
    assert project_id

    project_response = client.get(f"/api/projects/{project_id}")
    assert project_response.status_code == 200
    payload = project_response.json()
    assert payload["name"] == "脓毒症预后代谢组学研究"
    assert payload["topic"] == "脓毒症预后代谢组学相关研究"
    assert payload["description"] == "聚焦用于脓毒症预后判断的代谢组学研究与生物标志物证据。"
    assert payload["thread_profile"]["strategy"]["research_need"].startswith("Find metabolomics studies")
    assert payload["thread_profile"]["strategy"]["latest_task_id"] == task_payload["id"]
    assert payload["thread_profile"]["strategy"]["plan"]["screening_topic"] == "脓毒症预后代谢组学相关研究"
    assert payload["thread_profile"]["strategy"]["plan"]["intent_summary"] == "聚焦用于脓毒症预后判断的代谢组学研究与生物标志物证据。"
    assert payload["thread_profile"]["screening"]["topic"] == "脓毒症预后代谢组学相关研究"
    assert payload["thread_profile"]["screening"]["inclusion"] == ["人群脓毒症队列研究", "涉及代谢组学标志物"]


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

    screening_task = task_store.create_task(kind="screening", title="screening-review", metadata={"project_id": project["id"]})
    task_store.update(
        screening_task.task_id,
        status="succeeded",
        phase="completed",
        phase_label="Completed",
        records=[
            {
                "paper_id": payload["fulltext_queue"][0]["paper_id"],
                "title": "Paper One",
                "decision": "include",
                "confidence": 0.91,
                "reason": "高度相关，保留进入全文阶段",
                "year": 2024,
                "journal": "Journal A",
                "doi": "10.1000/paper-one",
            },
            {
                "paper_id": payload["fulltext_queue"][1]["paper_id"],
                "title": "Paper Two",
                "decision": "include",
                "confidence": 0.67,
                "reason": "相关性一般，待全文再确认",
                "year": 2025,
                "journal": "Journal B",
                "doi": "10.1000/paper-two",
            },
        ],
    )

    update = client.post(
        f"/api/projects/{project['id']}/fulltext/status",
        json={"paper_id": payload["fulltext_queue"][0]["paper_id"], "status": "ready", "note": "downloaded"},
    )
    assert update.status_code == 200
    updated_payload = update.json()
    ready_item = next(item for item in updated_payload["fulltext_queue"] if item["status"] == "ready")
    assert ready_item["note"] == "downloaded"
    assert ready_item["confidence"] == 0.91
    assert ready_item["screening_reason"] == "高度相关，保留进入全文阶段"
    ready_dataset = next(item for item in updated_payload["datasets"] if item["kind"] == "fulltext_ready")
    assert ready_dataset["record_count"] == 1

    exclude = client.post(
        f"/api/projects/{project['id']}/fulltext/status",
        json={"paper_id": payload["fulltext_queue"][1]["paper_id"], "status": "excluded", "note": "复审排除"},
    )
    assert exclude.status_code == 200
    excluded_payload = exclude.json()
    excluded_item = next(item for item in excluded_payload["fulltext_queue"] if item["paper_id"] == payload["fulltext_queue"][1]["paper_id"])
    assert excluded_item["status"] == "excluded"
    assert excluded_item["screening_reason"] == "相关性一般，待全文再确认"


def test_fulltext_queue_uses_imported_url_when_doi_missing(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="url-fallback-project", topic="topic", description="")
    ris_path = tmp_path / "url-fallback.ris"
    ris_path.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - CNKI Style Record",
                "JO  - Journal C",
                "PY  - 2022",
                "UR  - https://kns.cnki.net/example-record",
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
    payload = rebuild.json()
    assert len(payload["fulltext_queue"]) == 1
    assert payload["fulltext_queue"][0]["doi"] is None
    assert payload["fulltext_queue"][0]["landing_url"] == "https://kns.cnki.net/example-record"


def test_fulltext_queue_rebuild_uses_task_outputs_when_available(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="task-fulltext-project", topic="topic", description="")
    task = task_store.create_task(kind="screening", title="screening", metadata={})
    output_dir = task_store.tasks_dir / task.task_id / "screening_run"
    output_dir.mkdir(parents=True, exist_ok=True)
    task_store.update(task.task_id, output_dir=str(output_dir))

    record = PaperRecord(
        paper_id="paper_000042",
        title="CNKI Record",
        year=2024,
        journal="Journal",
        url="https://kns.cnki.net/example-record",
        authors=[],
        keywords=[],
        source_files=[],
        source_keys=[],
        merged_from=[],
        entry_type="article",
        status="included",
    )
    (output_dir / "deduped_records.json").write_text(
        json.dumps([record.model_dump(mode="json")], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "screening_decisions.json").write_text(
        json.dumps([{"paper_id": "paper_000042", "decision": "include"}], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    ris_path = output_dir / "included.ris"
    ris_path.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Some other title",
                "ER  - ",
            ]
        ),
        encoding="utf-8",
    )
    dataset = workspace_store.register_dataset(
        project_id=project["id"],
        task_id=task.task_id,
        kind="included",
        label="Included records",
        path=ris_path,
        record_count=1,
        file_format="ris",
    )

    rebuild = client.post(
        f"/api/projects/{project['id']}/fulltext/rebuild",
        json={"source_dataset_ids": [dataset["id"]]},
    )
    assert rebuild.status_code == 200
    payload = rebuild.json()
    assert payload["fulltext_queue"][0]["paper_id"] == "paper_000042"
    assert payload["fulltext_queue"][0]["candidate_id"].startswith("cand_")
    assert payload["fulltext_queue"][0]["landing_url"] == "https://kns.cnki.net/example-record"


def test_workbench_keeps_links_separate_when_source_tasks_reuse_paper_ids(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="collision-project", topic="topic", description="")

    def seed_screening_task(
        *,
        title: str,
        journal: str,
        year: int,
        paper_id: str,
        doi: str | None,
        url: str | None,
    ) -> dict:
        task = task_store.create_task(kind="screening", title=title, metadata={"project_id": project["id"]})
        output_dir = task_store.tasks_dir / task.task_id / "screening_run"
        output_dir.mkdir(parents=True, exist_ok=True)
        task_store.update(task.task_id, output_dir=str(output_dir))
        record = PaperRecord(
            paper_id=paper_id,
            title=title,
            year=year,
            journal=journal,
            doi=doi,
            url=url,
            authors=[],
            keywords=[],
            source_files=[],
            source_keys=[],
            merged_from=[],
            entry_type="article",
            status="included",
        )
        (output_dir / "deduped_records.json").write_text(
            json.dumps([record.model_dump(mode="json")], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output_dir / "screening_decisions.json").write_text(
            json.dumps([{"paper_id": paper_id, "decision": "include"}], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        ris_path = output_dir / "included.ris"
        ris_path.write_text(
            "\n".join(
                [
                    "TY  - JOUR",
                    f"TI  - {title}",
                    "ER  - ",
                ]
            ),
            encoding="utf-8",
        )
        return workspace_store.register_dataset(
            project_id=project["id"],
            task_id=task.task_id,
            kind="included",
            label=f"Included {title}",
            path=ris_path,
            record_count=1,
            file_format="ris",
        )

    english_dataset = seed_screening_task(
        title="Effects of Project Management Challenges on the Use of Sustainable Construction Materials: Evidence from Construction Industry Practitioners",
        journal="Construction Management Review",
        year=2024,
        paper_id="paper_000023",
        doi="10.1000/effects-project-management",
        url=None,
    )
    chinese_dataset = seed_screening_task(
        title="住宅建筑工程管理中的安全隐患及防范策略探讨",
        journal="建筑安全与管理",
        year=2023,
        paper_id="paper_000023",
        doi=None,
        url="https://kns.cnki.net/kcms2/article/example",
    )

    rebuild = client.post(
        f"/api/projects/{project['id']}/workbench/rebuild",
        json={"source_dataset_ids": [english_dataset["id"], chinese_dataset["id"]]},
    )
    assert rebuild.status_code == 200
    payload = rebuild.json()
    items = payload["workbench"]["items"]
    assert len(items) == 2

    by_title = {item["title"]: item for item in items}
    english_item = by_title[
        "Effects of Project Management Challenges on the Use of Sustainable Construction Materials: Evidence from Construction Industry Practitioners"
    ]
    chinese_item = by_title["住宅建筑工程管理中的安全隐患及防范策略探讨"]

    assert english_item["candidate_id"] != chinese_item["candidate_id"]
    assert english_item["preferred_open_url"] == "https://doi.org/10.1000/effects-project-management"
    assert chinese_item["preferred_open_url"] == "https://kns.cnki.net/kcms2/article/example"
    assert english_item["source_record_refs"][0]["paper_id"] == "paper_000023"
    assert chinese_item["source_record_refs"][0]["paper_id"] == "paper_000023"

    legacy_queue = payload["fulltext_queue"]
    assert len({item["paper_id"] for item in legacy_queue}) == 2
    assert {item["candidate_id"] for item in legacy_queue} == {english_item["candidate_id"], chinese_item["candidate_id"]}


def test_fulltext_queue_batch_status_update(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="batch-fulltext-project", topic="topic", description="")
    ris_path = tmp_path / "batch-fulltext.ris"
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
                "PY  - 2022",
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
    paper_ids = [item["paper_id"] for item in payload["fulltext_queue"]]

    response = client.post(
        f"/api/projects/{project['id']}/fulltext/status/batch",
        json={"paper_ids": paper_ids, "status": "excluded", "note": "批量复审排除"},
    )
    assert response.status_code == 200
    updated = response.json()
    assert all(item["status"] == "excluded" for item in updated["fulltext_queue"])
    assert all(item["note"] == "批量复审排除" for item in updated["fulltext_queue"])


def test_fulltext_queue_context_ignores_collision_from_excluded_other_round(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="context-project", topic="topic", description="")
    ris_path = tmp_path / "context-fulltext.ris"
    ris_path.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Matching Paper",
                "JO  - Journal A",
                "PY  - 2024",
                "DO  - 10.1000/matching-paper",
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
    payload = rebuild.json()
    paper_id = payload["fulltext_queue"][0]["paper_id"]

    matching_task = task_store.create_task(kind="screening", title="matching-round", metadata={"project_id": project["id"]})
    task_store.update(
        matching_task.task_id,
        status="succeeded",
        phase="completed",
        phase_label="Completed",
        records=[
            {
                "paper_id": "raw_999999",
                "title": "Matching Paper",
                "decision": "include",
                "confidence": 0.93,
                "reason": "高相关，建议进入全文阶段",
                "year": 2024,
                "journal": "Journal A",
                "doi": "10.1000/matching-paper",
            }
        ],
    )

    collision_task = task_store.create_task(kind="screening", title="collision-round", metadata={"project_id": project["id"]})
    task_store.update(
        collision_task.task_id,
        status="succeeded",
        phase="completed",
        phase_label="Completed",
        records=[
            {
                "paper_id": paper_id,
                "title": "Other Paper",
                "decision": "exclude",
                "confidence": 0.08,
                "reason": "这是另一轮里不相关的记录",
                "year": 2021,
                "journal": "Other Journal",
                "doi": "10.9999/other-paper",
            }
        ],
    )

    detail = client.get(f"/api/projects/{project['id']}")
    assert detail.status_code == 200
    item = detail.json()["fulltext_queue"][0]
    assert item["screening_decision"] == "include"
    assert item["screening_reason"] == "高相关，建议进入全文阶段"
    assert item["confidence"] == 0.93


def test_fulltext_queue_skips_items_later_marked_excluded_or_uncertain(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="latest-decision-project", topic="topic", description="")
    ris_path = tmp_path / "latest-decision.ris"
    ris_path.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Paper To Remove",
                "JO  - Journal Z",
                "PY  - 2023",
                "DO  - 10.1000/remove-me",
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
    assert len(rebuild.json()["fulltext_queue"]) == 1

    latest_task = task_store.create_task(kind="screening", title="latest-round", metadata={"project_id": project["id"]})
    task_store.update(
        latest_task.task_id,
        status="succeeded",
        phase="completed",
        phase_label="Completed",
        records=[
            {
                "paper_id": "raw_111111",
                "title": "Paper To Remove",
                "decision": "exclude",
                "confidence": 0.11,
                "reason": "后续轮次确认不纳入全文阶段",
                "year": 2023,
                "journal": "Journal Z",
                "doi": "10.1000/remove-me",
            }
        ],
    )

    detail = client.get(f"/api/projects/{project['id']}")
    assert detail.status_code == 200
    assert detail.json()["fulltext_queue"] == []


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


def test_screening_task_detail_exposes_uploaded_file_names_for_edit_restore(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)
    monkeypatch.setattr(app_module.TASK_STORE, "run_in_background", lambda task, worker: None)

    response = client.post(
        "/api/screening/tasks",
        data={
            "title": "restore-edit-task",
            "topic": "robot screening",
            "criteria_markdown": "# 研究主题\n\nrobot screening",
            "inclusion_json": json.dumps(["robot"]),
            "exclusion_json": json.dumps(["review"]),
            "source_dataset_ids_json": "[]",
            "provider": "deepseek",
            "model_name": "deepseek-chat",
            "api_base_url": "https://api.deepseek.com/v1",
            "api_key_env": "DEEPSEEK_API_KEY",
            "api_key": "",
            "temperature": "0",
            "max_tokens": "512",
            "min_request_interval_seconds": "1",
            "batch_size": "10",
            "stop_when_target_reached": "false",
            "allow_uncertain": "true",
            "retry_times": "2",
            "request_timeout_seconds": "60",
            "encoding": "auto",
        },
        files=[("files", ("CNKI-restore.net", b"%0 Journal Article\n%T example\n", "text/plain"))],
    )
    assert response.status_code == 200
    task_id = response.json()["id"]

    detail_response = client.get(f"/api/tasks/{task_id}")
    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["request_payload"]["uploaded_file_names"] == ["CNKI-restore.net"]


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


def test_workbench_report_source_tracks_final_includes(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="report-source-project", topic="topic", description="")
    ris_path = tmp_path / "report-source.ris"
    ris_path.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Candidate For Report",
                "JO  - Journal A",
                "PY  - 2024",
                "VL  - 36",
                "IS  - 3",
                "SP  - 89",
                "EP  - 93",
                "DO  - 10.1000/report-candidate",
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
        f"/api/projects/{project['id']}/workbench/rebuild",
        json={"source_dataset_ids": [dataset["id"]]},
    )
    assert rebuild.status_code == 200
    candidate_id = rebuild.json()["workbench"]["items"][0]["candidate_id"]

    update = client.post(
        f"/api/projects/{project['id']}/workbench/items/{candidate_id}",
        json={"access_status": "ready", "final_decision": "include", "access_note": "downloaded"},
    )
    assert update.status_code == 200
    payload = update.json()

    assert payload["workbench"]["summary"]["report_included"] == 1
    ready_dataset = next(item for item in payload["datasets"] if item["kind"] == "fulltext_ready")
    report_dataset = next(item for item in payload["datasets"] if item["kind"] == "report_source")
    assert ready_dataset["record_count"] == 1
    assert report_dataset["record_count"] == 1
    report_content = Path(report_dataset["path"]).read_text(encoding="utf-8")
    assert "Candidate For Report" in report_content
    assert "VL  - 36" in report_content
    assert "IS  - 3" in report_content
    assert "SP  - 89" in report_content
    assert "EP  - 93" in report_content


def test_report_task_normalizes_reasoner_max_tokens(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)
    monkeypatch.setattr(task_store, "run_in_background", lambda task, worker: None)

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

    rebuild = client.post(
        f"/api/projects/{project['id']}/workbench/rebuild",
        json={"source_dataset_ids": [dataset["id"]]},
    )
    assert rebuild.status_code == 200
    candidate_id = rebuild.json()["workbench"]["items"][0]["candidate_id"]

    update = client.post(
        f"/api/projects/{project['id']}/workbench/items/{candidate_id}",
        json={"access_status": "ready", "final_decision": "include"},
    )
    assert update.status_code == 200

    response = client.post(
        "/api/report/tasks",
        json={
            "title": "report",
            "project_id": project["id"],
            "screening_task_id": None,
            "dataset_ids": ["report-source"],
            "project_topic": "topic",
            "report_name": "simple_report",
            "retry_times": 1,
            "timeout_seconds": 30,
            "reference_style": "gbt7714",
            "model": {
                "provider": "deepseek",
                "model_name": "deepseek-reasoner",
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
    stored_task = task_store.load_task(response.json()["id"])
    assert stored_task["metadata"]["request_payload"]["model"]["max_tokens"] == 4096


def test_workbench_batch_patch_updates_selected_candidates(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="workbench-batch-project", topic="topic", description="")
    ris_path = tmp_path / "workbench-batch.ris"
    ris_path.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Batch Candidate One",
                "JO  - Journal A",
                "PY  - 2024",
                "DO  - 10.1000/batch-one",
                "ER  - ",
                "TY  - JOUR",
                "TI  - Batch Candidate Two",
                "JO  - Journal B",
                "PY  - 2023",
                "DO  - 10.1000/batch-two",
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
        f"/api/projects/{project['id']}/workbench/rebuild",
        json={"source_dataset_ids": [dataset["id"]]},
    )
    assert rebuild.status_code == 200
    candidate_ids = [item["candidate_id"] for item in rebuild.json()["workbench"]["items"]]

    update = client.post(
        f"/api/projects/{project['id']}/workbench/items/batch",
        json={"candidate_ids": candidate_ids, "access_status": "ready", "final_decision": "include", "access_note": "batch updated"},
    )
    assert update.status_code == 200
    payload = update.json()

    assert payload["workbench"]["summary"]["report_included"] == 2
    assert payload["workbench"]["summary"]["ready_for_decision"] == 0
    for item in payload["workbench"]["items"]:
        assert item["access_status"] == "ready"
        assert item["final_decision"] == "include"
        assert item["access_note"] == "batch updated"


def test_workbench_load_recovers_legacy_ready_state_from_stale_workbench_file(tmp_path: Path, monkeypatch) -> None:
    task_store = TaskStore(tmp_path / "api_runs")
    workspace_store = WorkspaceStore(tmp_path / "api_runs")
    monkeypatch.setattr(app_module, "TASK_STORE", task_store)
    monkeypatch.setattr(app_module, "WORKSPACE_STORE", workspace_store)

    project = workspace_store.create_project(name="legacy-recovery-project", topic="topic", description="")
    ris_path = tmp_path / "legacy-recovery.ris"
    ris_path.write_text(
        "\n".join(
            [
                "TY  - JOUR",
                "TI  - Legacy Recovery Candidate",
                "JO  - Journal A",
                "PY  - 2024",
                "DO  - 10.1000/legacy-recovery",
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
        f"/api/projects/{project['id']}/workbench/rebuild",
        json={"source_dataset_ids": [dataset["id"]]},
    )
    assert rebuild.status_code == 200
    rebuilt_payload = rebuild.json()
    rebuilt_item = rebuilt_payload["workbench"]["items"][0]

    stale_workbench = workspace_store.load_workbench(project["id"])
    stale_workbench["items"][0]["access_status"] = "pending"
    stale_workbench["items"][0]["access_note"] = ""
    stale_workbench["items"][0]["manual_pdf_url"] = None
    workspace_store.save_workbench(project["id"], stale_workbench)

    derived_dir = tmp_path / "api_runs" / "projects" / project["id"] / "derived"
    (derived_dir / "fulltext_queue.json").write_text(
        json.dumps(
            {
                "source_dataset_ids": [dataset["id"]],
                "items": [
                    {
                        "paper_id": "paper_000001",
                        "candidate_id": rebuilt_item["candidate_id"],
                        "title": "Legacy Recovery Candidate",
                        "journal": "Journal A",
                        "year": 2024,
                        "doi": "10.1000/legacy-recovery",
                        "status": "ready",
                        "note": "legacy recovered",
                        "source_url": None,
                        "pdf_url": "https://downloads.example.com/10.1000/legacy-recovery.pdf",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (derived_dir / "fulltext_statuses.json").write_text(
        json.dumps(
            {
                "paper_000001": {
                    "status": "ready",
                    "note": "legacy recovered",
                    "pdf_url": "https://downloads.example.com/10.1000/legacy-recovery.pdf",
                    "updated_at": "2026-04-15T18:00:00+08:00",
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    detail = client.get(f"/api/projects/{project['id']}")
    assert detail.status_code == 200
    item = detail.json()["workbench"]["items"][0]

    assert item["access_status"] == "ready"
    assert item["access_note"] == "legacy recovered"
    assert item["preferred_pdf_url"] == "https://downloads.example.com/10.1000/legacy-recovery.pdf"


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
