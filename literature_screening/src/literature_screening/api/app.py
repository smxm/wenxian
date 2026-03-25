from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from literature_screening.api.schemas import DatasetRecord, FulltextQueueItem, FulltextQueueRebuildRequest, FulltextStatusUpdateRequest, ProjectCreate, ProjectDetail, ProjectSnapshot, ProjectUpdate, StrategyPlan
from literature_screening.api.schemas import BulkReviewOverrideRequest, ReferenceOverrideRequest, ReportTaskCreate, RetryTaskRequest, ReviewOverrideRequest, StrategyTaskCreate, TaskArtifact
from literature_screening.api.schemas import TaskDetail, TaskEvent, TaskSnapshot, TaskTemplateRecord
from literature_screening.api.secret_store import SecretStore
from literature_screening.api.task_store import StoredTask, TaskStore
from literature_screening.api.template_store import TemplateStore
from literature_screening.api.workspace_store import WorkspaceStore
from literature_screening.studio.service import CriteriaDraft, ModelDraft, ReportJobRequest, StrategyJobRequest
from literature_screening.studio.service import ScreeningJobRequest, generate_simple_report_job, generate_strategy_job
from literature_screening.studio.service import prepare_virtual_screening_output_from_dataset_paths
from literature_screening.studio.service import load_screening_records, run_screening_job, save_uploaded_file_bytes


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

API_RUNS_ROOT = PROJECT_ROOT / "data" / "api_runs"
TASK_STORE = TaskStore(API_RUNS_ROOT)
WORKSPACE_STORE = WorkspaceStore(API_RUNS_ROOT)
TEMPLATE_STORE = TemplateStore(API_RUNS_ROOT)
SECRET_STORE = SecretStore()

app = FastAPI(title="Literature Screening Studio API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/meta")
def meta() -> dict:
    return {
        "providers": [
            {
                "provider": "deepseek",
                "label": "DeepSeek",
                "defaultModel": "deepseek-chat",
                "defaultBaseUrl": "https://api.deepseek.com/v1",
                "defaultApiKeyEnv": "DEEPSEEK_API_KEY",
            },
            {
                "provider": "kimi",
                "label": "Kimi",
                "defaultModel": "moonshot-v1-auto",
                "defaultBaseUrl": "https://api.moonshot.cn/v1",
                "defaultApiKeyEnv": "KIMI_API_KEY",
            },
        ],
        "referenceStyles": [
            {"value": "gbt7714", "label": "GB/T 7714"},
            {"value": "apa7", "label": "APA 7"},
        ],
        "acceptedInputFormats": [".bib", ".ris", ".enw", ".txt"],
        "strategyDefaults": {
            "provider": "deepseek",
            "model_name": "deepseek-reasoner",
            "api_base_url": "https://api.deepseek.com/v1",
            "api_key_env": "DEEPSEEK_API_KEY",
            "temperature": 0,
            "max_tokens": 4096,
            "min_request_interval_seconds": 2,
            "databases": [
                {"value": "scopus", "label": "Scopus 高级检索"},
                {"value": "wos", "label": "Web of Science 高级检索"},
                {"value": "pubmed", "label": "PubMed 高级检索"},
                {"value": "cnki", "label": "知网高级检索（篇关摘）"},
            ],
        },
    }


@app.get("/api/projects", response_model=list[ProjectSnapshot])
def list_projects() -> list[ProjectSnapshot]:
    return [ProjectSnapshot.model_validate(item) for item in WORKSPACE_STORE.list_projects()]


@app.post("/api/projects", response_model=ProjectSnapshot)
def create_project(request: ProjectCreate) -> ProjectSnapshot:
    project = WORKSPACE_STORE.create_project(name=request.name, topic=request.topic, description=request.description)
    return ProjectSnapshot.model_validate(project | {"dataset_count": 0})


@app.put("/api/projects/{project_id}", response_model=ProjectSnapshot)
def update_project(project_id: str, request: ProjectUpdate) -> ProjectSnapshot:
    project = WORKSPACE_STORE.update_project(
        project_id,
        name=request.name,
        topic=request.topic,
        description=request.description,
    )
    return ProjectSnapshot.model_validate(project | {"dataset_count": len(WORKSPACE_STORE.list_project_datasets(project_id))})


@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str) -> dict[str, str]:
    WORKSPACE_STORE.load_project(project_id)
    related_tasks = [task for task in TASK_STORE.list_tasks() if _task_project_id(task) == project_id]
    for task in related_tasks:
        TASK_STORE.delete_task(task["id"])
    WORKSPACE_STORE.delete_project(project_id)
    return {"status": "deleted"}


@app.get("/api/projects/{project_id}", response_model=ProjectDetail)
def get_project(project_id: str) -> ProjectDetail:
    project = WORKSPACE_STORE.load_project(project_id)
    tasks = [_to_snapshot(task) for task in TASK_STORE.list_tasks() if _task_project_id(task) == project_id]
    datasets = [DatasetRecord.model_validate(item) for item in WORKSPACE_STORE.list_project_datasets(project_id)]
    fulltext_queue = WORKSPACE_STORE.load_fulltext_queue(project_id)
    if not fulltext_queue.get("items") and any(dataset.kind in {"cumulative_included", "included_reviewed", "included"} for dataset in datasets):
        fulltext_queue = WORKSPACE_STORE.rebuild_fulltext_queue(project_id)
        datasets = [DatasetRecord.model_validate(item) for item in WORKSPACE_STORE.list_project_datasets(project_id)]
    return ProjectDetail.model_validate(
        project
        | {
            "dataset_count": len(datasets),
            "tasks": tasks,
            "datasets": datasets,
            "fulltext_queue": [FulltextQueueItem.model_validate(item) for item in fulltext_queue.get("items", [])],
            "fulltext_source_dataset_ids": fulltext_queue.get("source_dataset_ids", []),
        }
    )


@app.get("/api/datasets/{dataset_id}", response_model=DatasetRecord)
def get_dataset(dataset_id: str) -> DatasetRecord:
    dataset = WORKSPACE_STORE.find_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetRecord.model_validate(dataset)


@app.post("/api/projects/{project_id}/fulltext/rebuild", response_model=ProjectDetail)
def rebuild_fulltext_queue(project_id: str, request: FulltextQueueRebuildRequest) -> ProjectDetail:
    WORKSPACE_STORE.load_project(project_id)
    if request.source_dataset_ids:
        for dataset_id in request.source_dataset_ids:
            dataset = _require_dataset(dataset_id)
            if dataset["project_id"] != project_id:
                raise HTTPException(status_code=400, detail="Selected datasets must belong to the current thread")
    WORKSPACE_STORE.rebuild_fulltext_queue(project_id, source_dataset_ids=request.source_dataset_ids)
    return get_project(project_id)


@app.post("/api/projects/{project_id}/fulltext/status", response_model=ProjectDetail)
def update_fulltext_status(project_id: str, request: FulltextStatusUpdateRequest) -> ProjectDetail:
    WORKSPACE_STORE.load_project(project_id)
    WORKSPACE_STORE.update_fulltext_status(
        project_id=project_id,
        paper_id=request.paper_id,
        status=request.status,
        note=request.note,
    )
    queue = WORKSPACE_STORE.load_fulltext_queue(project_id)
    WORKSPACE_STORE.rebuild_fulltext_queue(project_id, source_dataset_ids=queue.get("source_dataset_ids", []))
    return get_project(project_id)


@app.post("/api/projects/{project_id}/fulltext/enrich", response_model=ProjectDetail)
def enrich_fulltext_links(project_id: str) -> ProjectDetail:
    WORKSPACE_STORE.load_project(project_id)
    queue = WORKSPACE_STORE.load_fulltext_queue(project_id)
    items = queue.get("items", [])
    for item in items:
        doi = (item.get("doi") or "").strip()
        if not doi:
            continue
        if item.get("oa_status") and item.get("landing_url"):
            continue
        landing_url = item.get("doi_url")
        pdf_url = item.get("pdf_url")
        oa_status = item.get("oa_status") or "unknown"
        try:
            response = httpx.get(
                f"https://api.openalex.org/works/https://doi.org/{quote(doi, safe='')}",
                headers={"User-Agent": "literature-screening/0.2"},
                timeout=20.0,
            )
            if response.status_code == 200:
                payload = response.json()
                open_access = payload.get("open_access") or {}
                primary_location = payload.get("primary_location") or {}
                landing_url = (
                    primary_location.get("landing_page_url")
                    or open_access.get("oa_url")
                    or item.get("doi_url")
                )
                pdf_url = open_access.get("oa_url") or pdf_url
                oa_status = "oa" if open_access.get("is_oa") else "closed"
        except Exception:
            landing_url = landing_url or item.get("doi_url")
        WORKSPACE_STORE.update_fulltext_status(
            project_id=project_id,
            paper_id=item["paper_id"],
            status=item.get("status", "pending"),
            note=item.get("note", ""),
            landing_url=landing_url,
            pdf_url=pdf_url,
            oa_status=oa_status,
        )
    WORKSPACE_STORE.rebuild_fulltext_queue(project_id, source_dataset_ids=queue.get("source_dataset_ids", []))
    return get_project(project_id)


@app.get("/api/templates", response_model=list[TaskTemplateRecord])
def list_templates(project_id: str | None = None) -> list[TaskTemplateRecord]:
    return [TaskTemplateRecord.model_validate(item) for item in TEMPLATE_STORE.list_templates(project_id=project_id)]


@app.post("/api/templates", response_model=TaskTemplateRecord)
def create_template(
    name: str = Form(...),
    payload_json: str = Form(...),
    project_id: str | None = Form(None),
) -> TaskTemplateRecord:
    payload = json.loads(payload_json)
    template = TEMPLATE_STORE.create_template(name=name, payload=payload, project_id=project_id)
    return TaskTemplateRecord.model_validate(template)


@app.get("/api/tasks", response_model=list[TaskSnapshot])
def list_tasks(
    project_id: str | None = None,
    kind: str | None = None,
    status: str | None = None,
    q: str | None = None,
) -> list[TaskSnapshot]:
    tasks = TASK_STORE.list_tasks()
    if project_id is not None:
        tasks = [task for task in tasks if _task_project_id(task) == project_id]
    if kind is not None:
        tasks = [task for task in tasks if task["kind"] == kind]
    if status is not None:
        tasks = [task for task in tasks if task["status"] == status]
    if q:
        keyword = q.strip().lower()
        tasks = [
            task
            for task in tasks
            if any(
                keyword in str(value).lower()
                for value in [
                    task.get("title", ""),
                    task.get("phase", ""),
                    task.get("project_topic") or task.get("metadata", {}).get("project_topic", ""),
                    _task_project_id(task) or "",
                ]
            )
        ]
    return [_to_snapshot(task) for task in tasks]


@app.get("/api/tasks/{task_id}", response_model=TaskDetail)
def get_task(task_id: str) -> TaskDetail:
    task = _get_task_or_404(task_id)
    return _to_detail(task)


@app.post("/api/tasks/{task_id}/cancel", response_model=TaskSnapshot)
def cancel_task(task_id: str) -> TaskSnapshot:
    task = _get_task_or_404(task_id)
    if task["status"] not in {"pending", "running"}:
        raise HTTPException(status_code=400, detail="Only pending or running tasks can be cancelled")
    cancelled = TASK_STORE.cancel_task(task_id)
    return _to_snapshot(cancelled)


@app.post("/api/tasks/{task_id}/retry", response_model=TaskSnapshot)
def retry_task(task_id: str, request: RetryTaskRequest) -> TaskSnapshot:
    task = _get_task_or_404(task_id)
    kind = task["kind"]
    if task.get("status") not in {"failed", "cancelled"}:
        raise HTTPException(status_code=400, detail="Only failed or cancelled tasks can be retried")

    if kind == "strategy":
        payload = _strategy_request_from_task(task)

        def worker(stored_task: StoredTask) -> dict:
            result = generate_strategy_job(
                payload,
                progress_callback=lambda phase, label, current=None, total=None, message=None: TASK_STORE.update(
                    stored_task.task_id,
                    phase=phase,
                    phase_label=label,
                    progress_current=current,
                    progress_total=total,
                    progress_message=message,
                ),
            )
            return {
                "summary": result.summary,
                "project_id": _task_project_id(task),
                "project_topic": task.get("project_topic") or task.get("metadata", {}).get("project_topic"),
                "model_provider": task.get("model_provider") or task.get("metadata", {}).get("model_provider"),
                "run_root": str(result.run_root),
                "output_dir": str(result.output_dir),
                "markdown_preview": result.markdown,
                "artifacts": _collect_strategy_artifacts(result),
            }

    elif kind == "screening":
        payload = _screening_request_from_task(task)

        def worker(stored_task: StoredTask) -> dict:
            result = run_screening_job(
                payload,
                progress_callback=lambda phase, label, current=None, total=None, message=None: TASK_STORE.update(
                    stored_task.task_id,
                    phase=phase,
                    phase_label=label,
                    progress_current=current,
                    progress_total=total,
                    progress_message=message,
                ),
                cancel_callback=lambda: TASK_STORE.is_cancel_requested(stored_task.task_id),
            )
            artifacts = _collect_screening_artifacts(result)
            output_dataset_ids = _register_screening_datasets(
                project_id=_task_project_id(task),
                task_id=stored_task.task_id,
                result=result,
                artifacts=artifacts,
                source_dataset_ids=task.get("input_dataset_ids") or task.get("metadata", {}).get("input_dataset_ids", []),
            )
            WORKSPACE_STORE.rebuild_cumulative_included_dataset(_task_project_id(task))
            WORKSPACE_STORE.rebuild_fulltext_queue(_task_project_id(task))
            TASK_STORE.append_event(
                stored_task.task_id,
                kind="datasets-registered",
                message="Registered screening output datasets",
                metadata={"output_dataset_ids": output_dataset_ids},
            )
            return {
                "summary": result.summary,
                "project_id": _task_project_id(task),
                "project_topic": task.get("project_topic") or task.get("metadata", {}).get("project_topic"),
                "model_provider": task.get("model_provider") or task.get("metadata", {}).get("model_provider"),
                "parent_task_id": task.get("parent_task_id") or task.get("metadata", {}).get("parent_task_id"),
                "input_dataset_ids": task.get("input_dataset_ids") or task.get("metadata", {}).get("input_dataset_ids", []),
                "output_dataset_ids": output_dataset_ids,
                "run_root": str(result.run_root),
                "output_dir": str(result.output_dir),
                "records": result.records,
                "artifacts": artifacts,
            }

    elif kind == "report":
        payload = _report_request_from_task(task)

        def worker(stored_task: StoredTask) -> dict:
            result = generate_simple_report_job(
                payload,
                progress_callback=lambda phase, label, current=None, total=None, message=None: TASK_STORE.update(
                    stored_task.task_id,
                    phase=phase,
                    phase_label=label,
                    progress_current=current,
                    progress_total=total,
                    progress_message=message,
                ),
            )
            return {
                "summary": {"report_name": payload.report_name, "reference_style": payload.reference_style},
                "project_id": _task_project_id(task),
                "project_topic": task.get("project_topic") or task.get("metadata", {}).get("project_topic"),
                "model_provider": task.get("model_provider") or task.get("metadata", {}).get("model_provider"),
                "input_dataset_ids": task.get("input_dataset_ids") or task.get("metadata", {}).get("input_dataset_ids", []),
                "run_root": str(result.run_root),
                "output_dir": str(result.report_output_dir),
                "markdown_preview": result.markdown,
                "artifacts": _collect_report_artifacts(result),
            }

    else:
        raise HTTPException(status_code=400, detail="Unsupported task kind")

    updated = TASK_STORE.retry_in_background(task_id, worker)
    return _to_snapshot(updated)


@app.post("/api/tasks/{task_id}/review-overrides", response_model=TaskDetail)
def apply_review_override(task_id: str, request: ReviewOverrideRequest) -> TaskDetail:
    updated_task, reviewed_dataset_ids = _apply_review_overrides(
        task_id,
        [{"paper_id": request.paper_id, "decision": request.decision, "reason": request.reason}],
    )
    TASK_STORE.append_event(
        task_id,
        kind="manual-review",
        message=f"Reviewed {request.paper_id} -> {request.decision}",
        metadata={"paper_id": request.paper_id, "decision": request.decision, "output_dataset_ids": reviewed_dataset_ids},
    )
    return _to_detail(updated_task)


@app.post("/api/tasks/{task_id}/review-overrides/bulk", response_model=TaskDetail)
def apply_bulk_review_override(task_id: str, request: BulkReviewOverrideRequest) -> TaskDetail:
    task = _get_task_or_404(task_id)
    if task["kind"] != "screening" or task["status"] != "succeeded":
        raise HTTPException(status_code=400, detail="Only completed screening tasks support manual review")

    matched_overrides, unmatched_titles = _build_bulk_review_overrides(
        rows=task.get("records", []),
        entries_text=request.entries_text,
        decision=request.decision,
        reason=request.reason,
    )
    if not matched_overrides:
        raise HTTPException(status_code=400, detail="No matching papers were found for the provided titles")

    updated_task, reviewed_dataset_ids = _apply_review_overrides(task_id, matched_overrides)
    TASK_STORE.append_event(
        task_id,
        kind="bulk-manual-review",
        message=f"Bulk reviewed {len(matched_overrides)} papers -> {request.decision}",
        metadata={
            "paper_ids": [item["paper_id"] for item in matched_overrides],
            "decision": request.decision,
            "unmatched_titles": unmatched_titles,
            "output_dataset_ids": reviewed_dataset_ids,
        },
    )
    return _to_detail(updated_task)


def _apply_review_overrides(task_id: str, overrides: list[dict[str, str]]) -> tuple[dict, list[str]]:
    task = _get_task_or_404(task_id)
    if task["kind"] != "screening" or task["status"] != "succeeded":
        raise HTTPException(status_code=400, detail="Only completed screening tasks support manual review")

    output_dir = Path(task["output_dir"])
    reviewed_dir = output_dir / "reviewed"
    reviewed_decisions_path = reviewed_dir / "screening_decisions.reviewed.json"
    original_decisions_path = output_dir / "screening_decisions.json"
    decisions_path = reviewed_decisions_path if reviewed_decisions_path.exists() else original_decisions_path
    if not decisions_path.exists():
        raise HTTPException(status_code=404, detail="screening_decisions.json is missing")

    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    override_map = {item["paper_id"]: item for item in overrides}
    matched_paper_ids: set[str] = set()
    for decision in decisions:
        paper_id = str(decision.get("paper_id", ""))
        override = override_map.get(paper_id)
        if not override:
            continue
        decision["decision"] = override["decision"]
        decision["reason"] = override.get("reason") or decision.get("reason", "")
        matched_paper_ids.add(paper_id)
    if len(matched_paper_ids) != len(override_map):
        missing = sorted(set(override_map) - matched_paper_ids)
        raise HTTPException(status_code=404, detail=f"Paper not found in screening decisions: {', '.join(missing)}")

    reviewed_dir.mkdir(parents=True, exist_ok=True)
    reviewed_decisions_path.write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")

    task["records"] = _apply_review_decisions_to_rows(task.get("records", []), decisions)
    task["summary"] = _rebuild_summary_from_rows(task.get("summary") or {}, task["records"])

    included_records, excluded_records, uncertain_records = _collect_records_from_review(task["records"], output_dir)
    reviewed_artifacts = _write_review_artifacts(
        output_dir=reviewed_dir,
        included_records=included_records,
        excluded_records=excluded_records,
        uncertain_records=uncertain_records,
        decisions=decisions,
    )
    reviewed_dataset_ids = _register_review_datasets(
        project_id=_task_project_id(task),
        task_id=task_id,
        artifacts=reviewed_artifacts,
        source_dataset_ids=task.get("output_dataset_ids") or task.get("metadata", {}).get("output_dataset_ids", []),
        included_count=len(included_records),
        excluded_count=len(excluded_records),
    )
    task["artifacts"] = {**task.get("artifacts", {}), **reviewed_artifacts}
    task["summary"]["reviewed"] = True
    task["records"] = task["records"]
    updated_task = TASK_STORE.update(
        task_id,
        records=task["records"],
        summary=task["summary"],
        artifacts=task["artifacts"],
        output_dataset_ids=(task.get("output_dataset_ids") or task.get("metadata", {}).get("output_dataset_ids", [])) + reviewed_dataset_ids,
    )
    project_id = _task_project_id(task)
    if project_id:
        WORKSPACE_STORE.rebuild_cumulative_included_dataset(project_id)
        WORKSPACE_STORE.rebuild_fulltext_queue(project_id)
    return updated_task, reviewed_dataset_ids


@app.post("/api/tasks/{task_id}/reference-overrides", response_model=TaskDetail)
def apply_reference_override(task_id: str, request: ReferenceOverrideRequest) -> TaskDetail:
    task = _get_task_or_404(task_id)
    if task["kind"] != "report" or task["status"] != "succeeded":
        raise HTTPException(status_code=400, detail="Only completed report tasks support reference override")

    output_dir = Path(task["output_dir"])
    notes_path = output_dir / "paper_notes.json"
    report_path = output_dir / "literature_report.md"
    if not notes_path.exists() or not report_path.exists():
        raise HTTPException(status_code=404, detail="Report notes or markdown file is missing")

    note_payload = json.loads(notes_path.read_text(encoding="utf-8"))
    ordered_titles = [str(item.get("title", "")).strip() for item in note_payload if str(item.get("title", "")).strip()]
    if not ordered_titles:
        raise HTTPException(status_code=400, detail="Report note order is unavailable")

    reference_style = str((task.get("summary") or {}).get("reference_style", "gbt7714"))
    try:
        reordered_lines = _reorder_reference_entries(
            raw_text=request.references_text,
            ordered_titles=ordered_titles,
            reference_style=reference_style,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    original_markdown = report_path.read_text(encoding="utf-8")
    updated_markdown = _replace_reference_section(original_markdown, reordered_lines)

    reviewed_dir = output_dir / "reviewed"
    reviewed_dir.mkdir(parents=True, exist_ok=True)
    reviewed_report_path = reviewed_dir / "literature_report.reviewed.md"
    reviewed_refs_path = reviewed_dir / "references.reviewed.txt"
    reviewed_report_path.write_text(updated_markdown, encoding="utf-8")
    reviewed_refs_path.write_text("\n".join(reordered_lines).strip() + "\n", encoding="utf-8")

    artifacts = {
        **task.get("artifacts", {}),
        "literature_report_reviewed": {
            "path": str(reviewed_report_path),
            "filename": reviewed_report_path.name,
            "content_type": "text/markdown; charset=utf-8",
            "size_bytes": reviewed_report_path.stat().st_size,
        },
        "references_reviewed": {
            "path": str(reviewed_refs_path),
            "filename": reviewed_refs_path.name,
            "content_type": "text/plain; charset=utf-8",
            "size_bytes": reviewed_refs_path.stat().st_size,
        },
    }
    summary = {**(task.get("summary") or {}), "reference_override_applied": True}
    TASK_STORE.update(task_id, markdown_preview=updated_markdown, artifacts=artifacts, summary=summary)
    TASK_STORE.append_event(
        task_id,
        kind="reference-override",
        message=f"Reordered {len(reordered_lines)} references using manual override",
        metadata={"reference_style": reference_style, "count": len(reordered_lines)},
    )
    return _to_detail(TASK_STORE.load_task(task_id))


@app.post("/api/strategy/tasks", response_model=TaskSnapshot)
def create_strategy_task(request: StrategyTaskCreate) -> TaskSnapshot:
    project = _ensure_project(
        project_id=request.project_id,
        new_project_name=request.new_project_name or None,
        topic=request.project_topic,
        description=request.new_project_description,
        fallback_name=request.title,
    )
    api_key = (request.model.api_key or "").strip()
    secret_id = SECRET_STORE.put(api_key) if api_key else None
    task = TASK_STORE.create_task(
        kind="strategy",
        title=request.title,
        metadata={
            "project_id": project["id"],
            "project_topic": request.project_topic,
            "model_provider": request.model.provider,
            "request_payload": request.model_dump(mode="json"),
            "model_secret_id": secret_id,
        },
    )
    payload = StrategyJobRequest(
        project_name=request.title,
        project_topic=request.project_topic,
        research_need=request.research_need,
        selected_databases=request.selected_databases,
        model=ModelDraft(
            provider=request.model.provider,
            model_name=request.model.model_name,
            api_base_url=request.model.api_base_url,
            api_key_env=request.model.api_key_env,
            api_key=api_key or None,
            temperature=request.model.temperature,
            max_tokens=request.model.max_tokens,
            min_request_interval_seconds=request.model.min_request_interval_seconds,
        ),
        runs_root=API_RUNS_ROOT / "runs",
        run_root_override=task.root_dir / "strategy_run",
        timeout_seconds=request.timeout_seconds,
    )

    def worker(stored_task: StoredTask) -> dict:
        result = generate_strategy_job(
            payload,
            progress_callback=lambda phase, label, current=None, total=None, message=None: TASK_STORE.update(
                stored_task.task_id,
                phase=phase,
                phase_label=label,
                progress_current=current,
                progress_total=total,
                progress_message=message,
            ),
        )
        return {
            "summary": result.summary,
            "project_id": project["id"],
            "project_topic": request.project_topic,
            "model_provider": request.model.provider,
            "run_root": str(result.run_root),
            "output_dir": str(result.output_dir),
            "markdown_preview": result.markdown,
            "artifacts": _collect_strategy_artifacts(result),
        }

    TASK_STORE.run_in_background(task, worker)
    return _to_snapshot(TASK_STORE.load_task(task.task_id))


@app.get("/api/tasks/{task_id}/artifacts/{artifact_key}")
def download_artifact(task_id: str, artifact_key: str) -> FileResponse:
    task = _get_task_or_404(task_id)
    artifacts = task.get("artifacts", {})
    artifact = artifacts.get(artifact_key)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    path = Path(artifact["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact file is missing")
    return FileResponse(path, media_type=artifact.get("content_type"), filename=artifact.get("filename"))


@app.post("/api/screening/tasks", response_model=TaskSnapshot)
async def create_screening_task(
    title: str = Form(...),
    topic: str = Form(...),
    criteria_markdown: str = Form(""),
    inclusion_json: str = Form(...),
    exclusion_json: str = Form(...),
    provider: str = Form(...),
    model_name: str = Form(...),
    api_base_url: str = Form(...),
    api_key_env: str = Form(...),
    api_key: str = Form(""),
    temperature: float = Form(0.0),
    max_tokens: int = Form(1536),
    min_request_interval_seconds: float = Form(2.0),
    batch_size: int = Form(10),
    target_include_count: int = Form(9999),
    stop_when_target_reached: bool = Form(False),
    allow_uncertain: bool = Form(True),
    retry_times: int = Form(6),
    request_timeout_seconds: int = Form(240),
    encoding: str = Form("auto"),
    project_id: str | None = Form(None),
    new_project_name: str | None = Form(None),
    new_project_description: str = Form(""),
    source_dataset_ids_json: str = Form("[]"),
    parent_task_id: str | None = Form(None),
    files: list[UploadFile] | None = File(None),
) -> TaskSnapshot:
    inclusion = json.loads(inclusion_json)
    exclusion = json.loads(exclusion_json)
    source_dataset_ids = json.loads(source_dataset_ids_json)
    project = _ensure_project(project_id=project_id, new_project_name=new_project_name, topic=topic, description=new_project_description, fallback_name=title)

    input_paths: list[Path] = []
    for dataset_id in source_dataset_ids:
        dataset = WORKSPACE_STORE.find_dataset(dataset_id)
        if dataset is None:
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
        if dataset["project_id"] != project["id"]:
            raise HTTPException(status_code=400, detail="All source datasets must belong to the selected project")
        input_paths.append(Path(dataset["path"]))

    secret_id = SECRET_STORE.put(api_key.strip()) if api_key.strip() else None
    task = TASK_STORE.create_task(
        kind="screening",
        title=title,
        metadata={
            "project_id": project["id"],
            "project_topic": topic,
            "model_provider": provider,
            "parent_task_id": parent_task_id,
            "input_dataset_ids": source_dataset_ids,
            "request_payload": {
                "title": title,
                "topic": topic,
                "criteria_markdown": criteria_markdown,
                "inclusion": inclusion,
                "exclusion": exclusion,
                "provider": provider,
                "model_name": model_name,
                "api_base_url": api_base_url,
                "api_key_env": api_key_env,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "min_request_interval_seconds": min_request_interval_seconds,
                "batch_size": batch_size,
                "target_include_count": target_include_count,
                "stop_when_target_reached": stop_when_target_reached,
                "allow_uncertain": allow_uncertain,
                "retry_times": retry_times,
                "request_timeout_seconds": request_timeout_seconds,
                "encoding": encoding,
                "project_id": project["id"],
                "parent_task_id": parent_task_id,
                "source_dataset_ids": source_dataset_ids,
            },
            "model_secret_id": secret_id,
        },
    )
    uploads_dir = task.root_dir / "uploads"
    uploaded_paths = save_uploaded_file_bytes(
        [(upload.filename or "upload.bin", await upload.read()) for upload in (files or [])],
        uploads_dir,
    )
    TASK_STORE.update(
        task.task_id,
        metadata={
            **task.payload["metadata"],
            "uploaded_input_paths": [str(path) for path in uploaded_paths],
        },
    )
    input_paths.extend(uploaded_paths)
    if not input_paths:
        raise HTTPException(status_code=400, detail="At least one uploaded file or source dataset is required")

    payload = ScreeningJobRequest(
        project_name=title,
        input_paths=input_paths,
        criteria=CriteriaDraft(topic=topic, inclusion=inclusion, exclusion=exclusion),
        model=ModelDraft(
            provider=provider,
            model_name=model_name,
            api_base_url=api_base_url,
            api_key_env=api_key_env,
            api_key=api_key.strip() or None,
            temperature=temperature,
            max_tokens=max_tokens,
            min_request_interval_seconds=min_request_interval_seconds,
        ),
        runs_root=API_RUNS_ROOT / "runs",
        batch_size=batch_size,
        target_include_count=target_include_count,
        stop_when_target_reached=stop_when_target_reached,
        allow_uncertain=allow_uncertain,
        retry_times=retry_times,
        request_timeout_seconds=request_timeout_seconds,
        encoding=encoding,
    )
    payload.run_root_override = task.root_dir / "screening_run"

    def worker(stored_task: StoredTask) -> dict:
        result = run_screening_job(
            payload,
            progress_callback=lambda phase, label, current=None, total=None, message=None: TASK_STORE.update(
                stored_task.task_id,
                phase=phase,
                phase_label=label,
                progress_current=current,
                progress_total=total,
                progress_message=message,
            ),
            cancel_callback=lambda: TASK_STORE.is_cancel_requested(stored_task.task_id),
        )
        artifacts = _collect_screening_artifacts(result)
        output_dataset_ids = _register_screening_datasets(
            project_id=project["id"],
            task_id=stored_task.task_id,
            result=result,
            artifacts=artifacts,
            source_dataset_ids=source_dataset_ids,
        )
        WORKSPACE_STORE.rebuild_cumulative_included_dataset(project["id"])
        WORKSPACE_STORE.rebuild_fulltext_queue(project["id"])
        TASK_STORE.append_event(
            stored_task.task_id,
            kind="datasets-registered",
            message="Registered screening output datasets",
            metadata={"output_dataset_ids": output_dataset_ids},
        )
        return {
            "summary": result.summary,
            "project_id": project["id"],
            "project_topic": topic,
            "model_provider": provider,
            "parent_task_id": parent_task_id,
            "input_dataset_ids": source_dataset_ids,
            "output_dataset_ids": output_dataset_ids,
            "run_root": str(result.run_root),
            "output_dir": str(result.output_dir),
            "records": result.records,
            "artifacts": artifacts,
        }

    TASK_STORE.run_in_background(task, worker)
    return _to_snapshot(TASK_STORE.load_task(task.task_id))


@app.post("/api/report/tasks", response_model=TaskSnapshot)
def create_report_task(request: ReportTaskCreate) -> TaskSnapshot:
    source_dataset_ids = request.dataset_ids
    screening_task: dict | None = None
    source_screening_task_id: str | None = request.screening_task_id
    project_id: str | None = None
    screening_output_dir: Path | None = None
    dataset_paths: list[Path] = []
    shared_notes_cache_dir: Path | None = None
    datasets: list[dict] = []

    if request.screening_task_id:
        screening_task = _get_task_or_404(request.screening_task_id)
        if screening_task["kind"] != "screening" or screening_task["status"] != "succeeded":
            raise HTTPException(status_code=400, detail="Screening task is not ready for report generation")
        project_id = _task_project_id(screening_task)
        screening_output_dir = Path(screening_task["output_dir"])
        shared_notes_cache_dir = screening_output_dir.parent / "_report_cache"
        if not source_dataset_ids:
            source_dataset_ids = screening_task.get("output_dataset_ids", [])
    elif source_dataset_ids:
        datasets = [_resolve_report_dataset(request, dataset_id) for dataset_id in source_dataset_ids]
        project_ids = {item["project_id"] for item in datasets}
        if len(project_ids) != 1:
            raise HTTPException(status_code=400, detail="Selected datasets must belong to the same project")
        project_id = next(iter(project_ids))
        fulltext_ready_dataset = next((item for item in datasets if item["kind"] == "fulltext_ready"), None)
        if fulltext_ready_dataset is not None:
            rebuild_source_dataset_ids = (
                fulltext_ready_dataset.get("source_dataset_ids")
                or WORKSPACE_STORE.load_fulltext_queue(project_id).get("source_dataset_ids", [])
            )
            WORKSPACE_STORE.rebuild_fulltext_queue(project_id, source_dataset_ids=rebuild_source_dataset_ids)
            datasets = [_resolve_report_dataset(request, dataset_id, project_id=project_id) for dataset_id in source_dataset_ids]
        if not any((item.get("record_count") or 0) > 0 for item in datasets):
            raise HTTPException(
                status_code=400,
                detail="Selected report source is empty. Mark papers as 已获取全文 first, or choose a non-empty source.",
            )
        dataset_paths = [Path(item["path"]) for item in datasets]
        source_task_ids = [item.get("task_id") for item in datasets if item.get("task_id")]
        if source_task_ids and len(set(source_task_ids)) == 1:
            source_task = _get_task_or_404(source_task_ids[0])
            if source_task.get("kind") == "screening" and source_task.get("output_dir"):
                source_screening_task_id = source_task["id"]
                shared_notes_cache_dir = Path(source_task["output_dir"]).parent / "_report_cache"
    else:
        raise HTTPException(status_code=400, detail="A screening task or at least one dataset is required")

    if project_id is None:
        raise HTTPException(status_code=400, detail="Project context is missing")

    task = TASK_STORE.create_task(
        kind="report",
        title=request.title,
        metadata={
            "project_id": project_id,
            "project_topic": request.project_topic,
            "model_provider": request.model.provider,
            "source_screening_task_id": source_screening_task_id,
            "input_dataset_ids": source_dataset_ids,
            "request_payload": request.model_dump(mode="json", exclude={"model": {"api_key"}}),
            "virtual_dataset_paths": [str(path) for path in dataset_paths],
            "model_secret_id": SECRET_STORE.put(request.model.api_key.strip()) if (request.model.api_key or "").strip() else None,
        },
    )
    payload = ReportJobRequest(
        screening_output_dir=screening_output_dir,
        project_topic=request.project_topic,
        model=ModelDraft(
            provider=request.model.provider,
            model_name=request.model.model_name,
            api_base_url=request.model.api_base_url,
            api_key_env=request.model.api_key_env,
            api_key=(request.model.api_key or "").strip() or None,
            temperature=request.model.temperature,
            max_tokens=request.model.max_tokens,
            min_request_interval_seconds=request.model.min_request_interval_seconds,
        ),
        report_name=request.report_name,
        runs_root=API_RUNS_ROOT / "runs",
        retry_times=request.retry_times,
        timeout_seconds=request.timeout_seconds,
        reference_style=request.reference_style,
    )

    def worker(stored_task: StoredTask) -> dict:
        effective_screening_output_dir = screening_output_dir
        if effective_screening_output_dir is None:
            effective_screening_output_dir = prepare_virtual_screening_output_from_dataset_paths(
                dataset_paths,
                stored_task.root_dir / "virtual_screening_output",
            )
        _seed_report_note_cache_from_existing_reports(
            shared_notes_cache_dir=shared_notes_cache_dir,
            source_screening_task_id=source_screening_task_id,
            provider=request.model.provider,
            model_name=request.model.model_name,
        )
        result = generate_simple_report_job(
            ReportJobRequest(
                screening_output_dir=effective_screening_output_dir,
                project_topic=request.project_topic,
                model=payload.model,
                report_name=payload.report_name,
                runs_root=payload.runs_root,
                report_output_dir_override=stored_task.root_dir / "report_output",
                shared_notes_cache_dir=shared_notes_cache_dir,
                retry_times=payload.retry_times,
                timeout_seconds=payload.timeout_seconds,
                reference_style=payload.reference_style,
            ),
            progress_callback=lambda phase, label, current=None, total=None, message=None: TASK_STORE.update(
                stored_task.task_id,
                phase=phase,
                phase_label=label,
                progress_current=current,
                progress_total=total,
                progress_message=message,
            ),
        )
        return {
            "summary": {"report_name": request.report_name, "reference_style": request.reference_style},
            "project_id": project_id,
            "project_topic": request.project_topic,
            "model_provider": request.model.provider,
            "input_dataset_ids": source_dataset_ids,
            "run_root": str(result.run_root),
            "output_dir": str(result.report_output_dir),
            "markdown_preview": result.markdown,
            "artifacts": _collect_report_artifacts(result),
        }

    TASK_STORE.run_in_background(task, worker)
    return _to_snapshot(TASK_STORE.load_task(task.task_id))


def _ensure_project(
    *,
    project_id: str | None,
    new_project_name: str | None,
    topic: str,
    description: str,
    fallback_name: str,
) -> dict:
    if project_id:
        return WORKSPACE_STORE.load_project(project_id)
    name = (new_project_name or fallback_name).strip()
    return WORKSPACE_STORE.create_project(name=name, topic=topic, description=description)


def _require_dataset(dataset_id: str) -> dict:
    dataset = WORKSPACE_STORE.find_dataset(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    return dataset


def _resolve_report_dataset(request: ReportTaskCreate, dataset_id: str, *, project_id: str | None = None) -> dict:
    scoped_project_id = project_id or request.project_id
    if scoped_project_id:
        try:
            return WORKSPACE_STORE.load_dataset(scoped_project_id, dataset_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Dataset not found in current project: {dataset_id}") from None
    return _require_dataset(dataset_id)


def _register_screening_datasets(
    *,
    project_id: str,
    task_id: str,
    result,
    artifacts: dict,
    source_dataset_ids: list[str],
) -> list[str]:
    dataset_ids: list[str] = []
    summary = result.summary or {}
    candidates = [
        ("included_ris", "included", "Included records", summary.get("included_count")),
        ("excluded_ris", "excluded", "Excluded records", summary.get("excluded_count")),
        ("unused_ris", "unused", "Unused remaining records", summary.get("unused_count")),
    ]
    for artifact_key, kind, label, count in candidates:
        artifact = artifacts.get(artifact_key)
        if not artifact:
            continue
        dataset = WORKSPACE_STORE.register_dataset(
            project_id=project_id,
            task_id=task_id,
            kind=kind,
            label=label,
            path=Path(artifact["path"]),
            record_count=int(count) if count is not None else None,
            file_format=Path(artifact["path"]).suffix.lstrip("."),
            source_dataset_ids=source_dataset_ids,
        )
        dataset_ids.append(dataset["id"])
    return dataset_ids


def _register_review_datasets(
    *,
    project_id: str | None,
    task_id: str,
    artifacts: dict,
    source_dataset_ids: list[str],
    included_count: int | None = None,
    excluded_count: int | None = None,
) -> list[str]:
    if project_id is None:
        return []
    dataset_ids: list[str] = []
    candidates = [
        ("reviewed_included_ris", "included_reviewed", "Reviewed included records", included_count),
        ("reviewed_excluded_ris", "excluded_reviewed", "Reviewed excluded records", excluded_count),
    ]
    for artifact_key, kind, label, count in candidates:
        artifact = artifacts.get(artifact_key)
        if not artifact:
            continue
        dataset = WORKSPACE_STORE.register_dataset(
            project_id=project_id,
            task_id=task_id,
            kind=kind,
            label=label,
            path=Path(artifact["path"]),
            record_count=count,
            file_format=Path(artifact["path"]).suffix.lstrip("."),
            source_dataset_ids=source_dataset_ids,
            metadata={"generated_from_review": True},
        )
        dataset_ids.append(dataset["id"])
    return dataset_ids


def _reorder_reference_entries(*, raw_text: str, ordered_titles: list[str], reference_style: str) -> list[str]:
    entries = _parse_reference_entries(raw_text)
    if not entries:
        raise ValueError("没有识别到可用的参考文献条目。请粘贴完整的参考列表。")

    matched_entries: list[str] = []
    used_indexes: set[int] = set()
    missing_titles: list[str] = []

    for title in ordered_titles:
        match_index = _find_best_reference_match(title=title, entries=entries, used_indexes=used_indexes)
        if match_index is None:
            missing_titles.append(title)
            continue
        used_indexes.add(match_index)
        matched_entries.append(entries[match_index])

    if missing_titles:
        preview = "；".join(missing_titles[:3])
        suffix = " 等" if len(missing_titles) > 3 else ""
        raise ValueError(f"有 {len(missing_titles)} 篇文献在你粘贴的参考列表里没有匹配上：{preview}{suffix}")

    return _renumber_reference_entries(matched_entries, reference_style=reference_style)


def _parse_reference_entries(raw_text: str) -> list[str]:
    text = raw_text.replace("\r\n", "\n").strip()
    if not text:
        return []

    if re.search(r"(?m)^\s*\[\d+\]", text):
        entries: list[str] = []
        current: list[str] = []
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r"^\[\d+\]", stripped):
                if current:
                    entries.append(" ".join(current).strip())
                current = [stripped]
            else:
                current.append(stripped)
        if current:
            entries.append(" ".join(current).strip())
        return entries

    if "\n\n" in text:
        return [" ".join(block.splitlines()).strip() for block in re.split(r"\n\s*\n", text) if block.strip()]

    return [line.strip() for line in text.splitlines() if line.strip()]


def _build_bulk_review_overrides(
    *,
    rows: list[dict],
    entries_text: str,
    decision: str,
    reason: str,
) -> tuple[list[dict[str, str]], list[str]]:
    entries = _parse_reference_entries(entries_text)
    if not entries:
        return [], []

    prepared_rows = [
        {
            "paper_id": str(row.get("paper_id", "")).strip(),
            "title": str(row.get("title", "")).strip(),
            "normalized_title": _normalize_reference_match_text(str(row.get("title", "")).strip()),
        }
        for row in rows
        if str(row.get("paper_id", "")).strip() and str(row.get("title", "")).strip()
    ]
    row_title_map = {item["normalized_title"]: item for item in prepared_rows if item["normalized_title"]}

    overrides: list[dict[str, str]] = []
    unmatched_titles: list[str] = []
    used_paper_ids: set[str] = set()

    for entry in entries:
        candidate_title = _extract_reference_title(entry).strip()
        normalized_candidate = _normalize_reference_match_text(candidate_title)
        if not normalized_candidate:
            continue

        matched_row = row_title_map.get(normalized_candidate)
        if matched_row is None:
            best_match: dict | None = None
            best_score = 0.0
            for row in prepared_rows:
                if row["paper_id"] in used_paper_ids:
                    continue
                score = 0.0
                normalized_title = row["normalized_title"]
                if not normalized_title:
                    continue
                if normalized_candidate == normalized_title:
                    score = 1.0
                elif normalized_candidate in normalized_title or normalized_title in normalized_candidate:
                    score = 0.95
                else:
                    score = difflib.SequenceMatcher(None, normalized_candidate, normalized_title).ratio()
                if score > best_score:
                    best_match = row
                    best_score = score
            matched_row = best_match if best_score >= 0.6 else None

        if matched_row is None:
            unmatched_titles.append(candidate_title or entry.strip())
            continue

        if matched_row["paper_id"] in used_paper_ids:
            continue
        used_paper_ids.add(matched_row["paper_id"])
        overrides.append(
            {
                "paper_id": matched_row["paper_id"],
                "decision": decision,
                "reason": reason,
            }
        )

    return overrides, unmatched_titles


def _find_best_reference_match(*, title: str, entries: list[str], used_indexes: set[int]) -> int | None:
    normalized_title = _normalize_reference_match_text(title)
    if not normalized_title:
        return None

    best_index: int | None = None
    best_score = 0.0
    for index, entry in enumerate(entries):
        if index in used_indexes:
            continue
        candidate_title = _extract_reference_title(entry)
        normalized_candidate = _normalize_reference_match_text(candidate_title or entry)
        if not normalized_candidate:
            continue

        score = 0.0
        if normalized_title == normalized_candidate:
            score = 1.0
        elif normalized_title in normalized_candidate or normalized_candidate in normalized_title:
            score = 0.95
        else:
            score = difflib.SequenceMatcher(None, normalized_title, normalized_candidate).ratio()

        if score > best_score:
            best_index = index
            best_score = score

    if best_score >= 0.6:
        return best_index
    return None


def _extract_reference_title(entry: str) -> str:
    stripped = re.sub(r"^\s*\[\d+\]\s*", "", entry).strip()
    patterns = [
        r"^[^.]+\.\s*(.+?)\[[A-Za-z/]+\]\.",
        r"^\s*.+?\(\d{4}\)\.\s*(.+?)\.\s*(?:<|[A-Z][a-z])",
    ]
    for pattern in patterns:
        match = re.search(pattern, stripped)
        if match:
            return match.group(1).strip()
    return stripped


def _normalize_reference_match_text(text: str) -> str:
    lowered = text.lower()
    lowered = lowered.replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", lowered)


def _renumber_reference_entries(entries: list[str], *, reference_style: str) -> list[str]:
    cleaned = [re.sub(r"^\s*\[\d+\]\s*", "", entry).strip() for entry in entries]
    if reference_style == "apa7":
        return cleaned
    return [f"[{index}] {entry}" for index, entry in enumerate(cleaned, start=1)]


def _replace_reference_section(markdown: str, reference_lines: list[str]) -> str:
    marker = "# 参考列表"
    if marker not in markdown:
        raise ValueError("报告中没有找到“参考列表”章节。")
    head, _tail = markdown.split(marker, 1)
    body = "\n".join(reference_lines).strip()
    return f"{head.rstrip()}\n\n{marker}\n\n{body}\n"


def _get_task_or_404(task_id: str) -> dict:
    try:
        return TASK_STORE.load_task(task_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


def _task_project_id(task: dict) -> str | None:
    return task.get("project_id") or task.get("metadata", {}).get("project_id")


def _to_snapshot(task: dict) -> TaskSnapshot:
    artifacts = [_artifact_from_entry(key, value) for key, value in task.get("artifacts", {}).items()]
    return TaskSnapshot(
        id=task["id"],
        kind=task["kind"],
        status=task["status"],
        title=task["title"],
        phase=task["phase"],
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        summary=task.get("summary"),
        error=task.get("error"),
        phase_label=task.get("phase_label"),
        progress_current=task.get("progress_current"),
        progress_total=task.get("progress_total"),
        progress_message=task.get("progress_message"),
        project_id=_task_project_id(task),
        parent_task_id=task.get("parent_task_id") or task.get("metadata", {}).get("parent_task_id"),
        input_dataset_ids=task.get("input_dataset_ids") or task.get("metadata", {}).get("input_dataset_ids", []),
        output_dataset_ids=task.get("output_dataset_ids") or task.get("metadata", {}).get("output_dataset_ids", []),
        project_topic=task.get("project_topic") or task.get("metadata", {}).get("project_topic"),
        model_provider=task.get("model_provider") or task.get("metadata", {}).get("model_provider"),
        attempt_count=int(task.get("attempt_count", 0) or 0),
        artifacts=artifacts,
    )


def _to_detail(task: dict) -> TaskDetail:
    snapshot = _to_snapshot(task)
    return TaskDetail(
        **snapshot.model_dump(),
        run_root=task.get("run_root"),
        output_dir=task.get("output_dir"),
        records=_resolve_task_records(task),
        markdown_preview=task.get("markdown_preview"),
        events=[TaskEvent.model_validate(item) for item in TASK_STORE.load_events(task["id"])],
        strategy_plan=_resolve_strategy_plan(task),
        request_payload=task.get("metadata", {}).get("request_payload"),
    )


def _seed_report_note_cache_from_existing_reports(
    *,
    shared_notes_cache_dir: Path | None,
    source_screening_task_id: str | None,
    provider: str,
    model_name: str,
) -> None:
    if shared_notes_cache_dir is None or not source_screening_task_id:
        return

    cache_path = _report_notes_cache_path(shared_notes_cache_dir, provider=provider, model_name=model_name)
    notes_by_id: dict[str, dict] = {}
    if cache_path.exists():
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            notes_by_id = {item["paper_id"]: item for item in payload if item.get("paper_id")}
        except Exception:
            notes_by_id = {}

    candidate_tasks = [
        task
        for task in TASK_STORE.list_tasks()
        if task.get("kind") == "report"
        and task.get("status") == "succeeded"
        and (task.get("metadata", {}).get("source_screening_task_id") == source_screening_task_id)
    ]
    candidate_tasks.sort(key=lambda item: item.get("updated_at", ""))
    for task in candidate_tasks:
        request_payload = task.get("metadata", {}).get("request_payload") or {}
        model_payload = request_payload.get("model") or {}
        if (task.get("model_provider") or task.get("metadata", {}).get("model_provider")) != provider:
            continue
        if model_payload.get("model_name") != model_name:
            continue
        output_dir = task.get("output_dir")
        if not output_dir:
            continue
        notes_path = Path(output_dir) / "paper_notes.json"
        if not notes_path.exists():
            continue
        try:
            payload = json.loads(notes_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for item in payload:
            paper_id = item.get("paper_id")
            if paper_id:
                notes_by_id[paper_id] = item

    if not notes_by_id:
        return

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(list(notes_by_id.values()), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _report_notes_cache_path(shared_notes_cache_dir: Path, *, provider: str, model_name: str) -> Path:
    provider_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", provider).strip("-").lower() or "provider"
    model_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", model_name).strip("-").lower() or "model"
    return shared_notes_cache_dir / f"paper_notes_cache_{provider_slug}_{model_slug}_v1.json"


def _artifact_from_entry(key: str, payload: dict) -> TaskArtifact:
    return TaskArtifact(
        key=key,
        filename=payload["filename"],
        content_type=payload.get("content_type", "application/octet-stream"),
        size_bytes=payload.get("size_bytes"),
    )


def _resolve_task_records(task: dict) -> list[dict]:
    current_records = task.get("records", []) or []
    if task.get("kind") != "screening":
        return current_records

    output_dir = task.get("output_dir")
    if not output_dir:
        return current_records

    if current_records and all(record.get("abstract") for record in current_records):
        return current_records

    try:
        hydrated_records = load_screening_records(Path(output_dir))
    except Exception:
        return current_records

    if not current_records:
        return hydrated_records

    current_map = {record.get("paper_id"): record for record in current_records}
    merged: list[dict] = []
    for hydrated in hydrated_records:
        existing = current_map.get(hydrated.get("paper_id"))
        if existing:
            merged.append({**hydrated, **existing, "abstract": hydrated.get("abstract") or existing.get("abstract")})
        else:
            merged.append(hydrated)
    return merged


def _resolve_strategy_plan(task: dict) -> StrategyPlan | None:
    if task.get("kind") != "strategy":
        return None
    output_dir = task.get("output_dir")
    if not output_dir:
        return None
    plan_path = Path(output_dir) / "strategy_plan.json"
    if not plan_path.exists():
        return None
    try:
        payload = json.loads(plan_path.read_text(encoding="utf-8"))
        return StrategyPlan.model_validate(payload)
    except Exception:
        return None


def _collect_screening_artifacts(result) -> dict:
    content_types = {
        ".md": "text/markdown; charset=utf-8",
        ".json": "application/json",
        ".ris": "application/x-research-info-systems",
        ".bib": "application/x-bibtex",
    }
    paths = {
        "included_report": result.reports["included_report"],
        "excluded_report": result.reports["excluded_report"],
        "uncertain_report": result.reports["uncertain_report"],
        "included_ris": result.reports["included_ris"],
        "excluded_ris": result.reports["excluded_ris"],
        "unused_ris": result.reports["unused_ris"],
        "included_bib": result.reports["included_bib"],
        "excluded_bib": result.reports["excluded_bib"],
        "unused_bib": result.reports["unused_bib"],
        "run_summary": result.output_dir / "run_summary.json",
        "screening_decisions": result.output_dir / "screening_decisions.json",
    }
    artifacts: dict[str, dict] = {}
    for key, path in paths.items():
        if path.exists():
            artifacts[key] = {
                "path": str(path),
                "filename": path.name,
                "content_type": content_types.get(path.suffix.lower(), "application/octet-stream"),
                "size_bytes": path.stat().st_size,
            }
    return artifacts


def _collect_strategy_artifacts(result) -> dict:
    content_types = {
        ".md": "text/markdown; charset=utf-8",
        ".json": "application/json",
        ".txt": "text/plain; charset=utf-8",
    }
    artifacts: dict[str, dict] = {}
    for key, path in result.artifacts.items():
        if path.exists():
            artifacts[key] = {
                "path": str(path),
                "filename": path.name,
                "content_type": content_types.get(path.suffix.lower(), "application/octet-stream"),
                "size_bytes": path.stat().st_size,
            }
    return artifacts


def _collect_report_artifacts(result) -> dict:
    artifacts = {
        "literature_report": {
            "path": str(result.report_path),
            "filename": result.report_path.name,
            "content_type": "text/markdown; charset=utf-8",
            "size_bytes": result.report_path.stat().st_size if result.report_path.exists() else None,
        },
        "paper_notes": {
            "path": str(result.notes_path),
            "filename": result.notes_path.name,
            "content_type": "application/json",
            "size_bytes": result.notes_path.stat().st_size if result.notes_path.exists() else None,
        },
    }
    overview_path = result.report_output_dir / "report_overview.json"
    if overview_path.exists():
        artifacts["report_overview"] = {
            "path": str(overview_path),
            "filename": overview_path.name,
            "content_type": "application/json",
            "size_bytes": overview_path.stat().st_size,
        }
    return artifacts


def _strategy_request_from_task(task: dict) -> StrategyJobRequest:
    metadata = task.get("metadata", {})
    payload = metadata.get("request_payload", {})
    api_key = SECRET_STORE.get(metadata.get("model_secret_id"))
    return StrategyJobRequest(
        project_name=payload["title"],
        project_topic=payload["project_topic"],
        research_need=payload["research_need"],
        selected_databases=payload["selected_databases"],
        model=ModelDraft(
            provider=payload["model"]["provider"],
            model_name=payload["model"]["model_name"],
            api_base_url=payload["model"]["api_base_url"],
            api_key_env=payload["model"]["api_key_env"],
            api_key=api_key,
            temperature=payload["model"]["temperature"],
            max_tokens=payload["model"]["max_tokens"],
            min_request_interval_seconds=payload["model"]["min_request_interval_seconds"],
        ),
        runs_root=API_RUNS_ROOT / "runs",
        run_root_override=TASK_STORE.tasks_dir / task["id"] / "strategy_run",
        timeout_seconds=payload["timeout_seconds"],
    )


def _screening_request_from_task(task: dict) -> ScreeningJobRequest:
    metadata = task.get("metadata", {})
    payload = metadata.get("request_payload", {})
    api_key = SECRET_STORE.get(metadata.get("model_secret_id"))
    input_paths = [Path(item) for item in metadata.get("uploaded_input_paths", [])]
    for dataset_id in payload.get("source_dataset_ids", []):
        dataset = _require_dataset(dataset_id)
        input_paths.append(Path(dataset["path"]))
    return ScreeningJobRequest(
        project_name=payload["title"],
        input_paths=input_paths,
        criteria=CriteriaDraft(
            topic=payload["topic"],
            inclusion=payload["inclusion"],
            exclusion=payload["exclusion"],
        ),
        model=ModelDraft(
            provider=payload["provider"],
            model_name=payload["model_name"],
            api_base_url=payload["api_base_url"],
            api_key_env=payload["api_key_env"],
            api_key=api_key,
            temperature=payload["temperature"],
            max_tokens=payload["max_tokens"],
            min_request_interval_seconds=payload["min_request_interval_seconds"],
        ),
        runs_root=API_RUNS_ROOT / "runs",
        run_root_override=(TASK_STORE.tasks_dir / task["id"] / "screening_run"),
        batch_size=payload["batch_size"],
        target_include_count=payload["target_include_count"],
        stop_when_target_reached=payload["stop_when_target_reached"],
        allow_uncertain=payload["allow_uncertain"],
        retry_times=payload["retry_times"],
        request_timeout_seconds=payload["request_timeout_seconds"],
        encoding=payload["encoding"],
    )


def _report_request_from_task(task: dict) -> ReportJobRequest:
    metadata = task.get("metadata", {})
    payload = metadata.get("request_payload", {})
    api_key = SECRET_STORE.get(metadata.get("model_secret_id"))
    screening_output_dir = task.get("metadata", {}).get("source_screening_task_id")
    if payload.get("screening_task_id"):
        source_task = _get_task_or_404(payload["screening_task_id"])
        screening_output_path = Path(source_task["output_dir"])
    else:
        dataset_paths = [Path(item) for item in metadata.get("virtual_dataset_paths", [])]
        screening_output_path = prepare_virtual_screening_output_from_dataset_paths(
            dataset_paths,
            TASK_STORE.tasks_dir / task["id"] / "virtual_screening_output",
        )
    return ReportJobRequest(
        screening_output_dir=screening_output_path,
        project_topic=payload["project_topic"],
        model=ModelDraft(
            provider=payload["model"]["provider"],
            model_name=payload["model"]["model_name"],
            api_base_url=payload["model"]["api_base_url"],
            api_key_env=payload["model"]["api_key_env"],
            api_key=api_key,
            temperature=payload["model"]["temperature"],
            max_tokens=payload["model"]["max_tokens"],
            min_request_interval_seconds=payload["model"]["min_request_interval_seconds"],
        ),
        report_name=payload["report_name"],
        runs_root=API_RUNS_ROOT / "runs",
        report_output_dir_override=TASK_STORE.tasks_dir / task["id"] / "report_output",
        retry_times=payload["retry_times"],
        timeout_seconds=payload["timeout_seconds"],
        reference_style=payload["reference_style"],
    )


def _apply_review_decisions_to_rows(rows: list[dict], decisions: list[dict]) -> list[dict]:
    decision_map = {item["paper_id"]: item for item in decisions}
    updated_rows: list[dict] = []
    for row in rows:
        decision = decision_map.get(row["paper_id"])
        if decision is None:
            updated_rows.append(row)
            continue
        updated_rows.append(
            {
                **row,
                "decision": decision.get("decision", row.get("decision")),
                "reason": decision.get("reason", row.get("reason", "")),
                "confidence": decision.get("confidence", row.get("confidence")),
            }
        )
    return updated_rows


def _rebuild_summary_from_rows(summary: dict, rows: list[dict]) -> dict:
    next_summary = dict(summary)
    next_summary["included_count"] = sum(1 for row in rows if row.get("decision") == "include")
    next_summary["excluded_count"] = sum(1 for row in rows if row.get("decision") == "exclude")
    next_summary["uncertain_count"] = sum(1 for row in rows if row.get("decision") == "uncertain")
    next_summary["processed_count"] = len(rows)
    return next_summary


def _collect_records_from_review(rows: list[dict], output_dir: Path) -> tuple[list, list, list]:
    from literature_screening.core.models import PaperRecord

    deduped_path = output_dir / "deduped_records.json"
    if not deduped_path.exists():
        return [], [], []
    records = json.loads(deduped_path.read_text(encoding="utf-8"))
    record_map = {item["paper_id"]: PaperRecord.model_validate(item) for item in records}

    def pick(decision: str) -> list:
        return [record_map[row["paper_id"]] for row in rows if row.get("decision") == decision and row["paper_id"] in record_map]

    return pick("include"), pick("exclude"), pick("uncertain")


def _write_review_artifacts(
    *,
    output_dir: Path,
    included_records: list,
    excluded_records: list,
    uncertain_records: list,
    decisions: list[dict],
) -> dict:
    from literature_screening.bibtex.exporter import export_ris

    artifacts: dict[str, dict] = {}
    decisions_path = output_dir / "screening_decisions.reviewed.json"
    decisions_path.write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    artifacts["reviewed_decisions"] = {
        "path": str(decisions_path),
        "filename": decisions_path.name,
        "content_type": "application/json",
        "size_bytes": decisions_path.stat().st_size,
    }
    included_path = output_dir / "included.reviewed.ris"
    excluded_path = output_dir / "excluded.reviewed.ris"
    uncertain_path = output_dir / "uncertain.reviewed.md"
    if included_records:
        export_ris(included_records, included_path)
        artifacts["reviewed_included_ris"] = {
            "path": str(included_path),
            "filename": included_path.name,
            "content_type": "application/x-research-info-systems",
            "size_bytes": included_path.stat().st_size,
        }
    if excluded_records:
        export_ris(excluded_records, excluded_path)
        artifacts["reviewed_excluded_ris"] = {
            "path": str(excluded_path),
            "filename": excluded_path.name,
            "content_type": "application/x-research-info-systems",
            "size_bytes": excluded_path.stat().st_size,
        }
    if uncertain_records:
        uncertain_lines = ["# Reviewed Uncertain Papers", ""]
        for item in uncertain_records:
            uncertain_lines.append(f"## {item.title}")
            uncertain_lines.append("")
            uncertain_lines.append(f"- paper_id: {item.paper_id}")
            if item.doi:
                uncertain_lines.append(f"- doi: {item.doi}")
            if item.year is not None:
                uncertain_lines.append(f"- year: {item.year}")
            if item.journal:
                uncertain_lines.append(f"- journal: {item.journal}")
            uncertain_lines.append("")
        uncertain_path.write_text("\n".join(uncertain_lines), encoding="utf-8")
        artifacts["reviewed_uncertain_report"] = {
            "path": str(uncertain_path),
            "filename": uncertain_path.name,
            "content_type": "text/markdown; charset=utf-8",
            "size_bytes": uncertain_path.stat().st_size,
        }
    return artifacts
