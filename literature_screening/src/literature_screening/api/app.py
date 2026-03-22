from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from literature_screening.api.schemas import ReportTaskCreate
from literature_screening.api.schemas import TaskArtifact, TaskDetail, TaskSnapshot
from literature_screening.api.task_store import StoredTask, TaskStore
from literature_screening.studio.service import CriteriaDraft, ModelDraft, ReportJobRequest
from literature_screening.studio.service import ScreeningJobRequest, generate_simple_report_job
from literature_screening.studio.service import run_screening_job, save_uploaded_file_bytes


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

API_RUNS_ROOT = PROJECT_ROOT / "data" / "api_runs"
TASK_STORE = TaskStore(API_RUNS_ROOT)

app = FastAPI(title="Literature Screening Studio API", version="0.1.0")
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
    }


@app.get("/api/tasks", response_model=list[TaskSnapshot])
def list_tasks() -> list[TaskSnapshot]:
    return [_to_snapshot(task) for task in TASK_STORE.list_tasks()]


@app.get("/api/tasks/{task_id}", response_model=TaskDetail)
def get_task(task_id: str) -> TaskDetail:
    task = _get_task_or_404(task_id)
    return _to_detail(task)


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
    inclusion_json: str = Form(...),
    exclusion_json: str = Form(...),
    provider: str = Form(...),
    model_name: str = Form(...),
    api_base_url: str = Form(...),
    api_key_env: str = Form(...),
    temperature: float = Form(0.0),
    max_tokens: int = Form(1536),
    min_request_interval_seconds: float = Form(2.0),
    batch_size: int = Form(20),
    target_include_count: int = Form(9999),
    stop_when_target_reached: bool = Form(False),
    allow_uncertain: bool = Form(True),
    retry_times: int = Form(6),
    request_timeout_seconds: int = Form(240),
    encoding: str = Form("auto"),
    files: list[UploadFile] = File(...),
) -> TaskSnapshot:
    inclusion = json.loads(inclusion_json)
    exclusion = json.loads(exclusion_json)
    task = TASK_STORE.create_task(
        kind="screening",
        title=title,
        metadata={
            "project_topic": topic,
            "model_provider": provider,
        },
    )
    uploads_dir = task.root_dir / "uploads"
    uploaded_paths = save_uploaded_file_bytes(
        [(upload.filename or "upload.bin", await upload.read()) for upload in files],
        uploads_dir,
    )
    payload = ScreeningJobRequest(
        project_name=title,
        input_paths=uploaded_paths,
        criteria=CriteriaDraft(topic=topic, inclusion=inclusion, exclusion=exclusion),
        model=ModelDraft(
            provider=provider,
            model_name=model_name,
            api_base_url=api_base_url,
            api_key_env=api_key_env,
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
        )
        return {
            "summary": result.summary,
            "project_topic": topic,
            "model_provider": provider,
            "run_root": str(result.run_root),
            "output_dir": str(result.output_dir),
            "records": result.records,
            "artifacts": _collect_screening_artifacts(result),
        }

    TASK_STORE.run_in_background(task, worker)
    return _to_snapshot(TASK_STORE.load_task(task.task_id))


@app.post("/api/report/tasks", response_model=TaskSnapshot)
def create_report_task(request: ReportTaskCreate) -> TaskSnapshot:
    screening_task = _get_task_or_404(request.screening_task_id)
    if screening_task["kind"] != "screening" or screening_task["status"] != "succeeded":
        raise HTTPException(status_code=400, detail="Screening task is not ready for report generation")

    task = TASK_STORE.create_task(
        kind="report",
        title=request.title,
        metadata={
            "project_topic": request.project_topic,
            "model_provider": request.model.provider,
            "source_screening_task_id": request.screening_task_id,
        },
    )
    payload = ReportJobRequest(
        screening_output_dir=Path(screening_task["output_dir"]),
        project_topic=request.project_topic,
        model=ModelDraft(
            provider=request.model.provider,
            model_name=request.model.model_name,
            api_base_url=request.model.api_base_url,
            api_key_env=request.model.api_key_env,
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
            "summary": {"report_name": request.report_name, "reference_style": request.reference_style},
            "project_topic": request.project_topic,
            "model_provider": request.model.provider,
            "run_root": str(result.run_root),
            "output_dir": str(result.report_output_dir),
            "markdown_preview": result.markdown,
            "artifacts": _collect_report_artifacts(result),
        }

    TASK_STORE.run_in_background(task, worker)
    return _to_snapshot(TASK_STORE.load_task(task.task_id))


def _get_task_or_404(task_id: str) -> dict:
    try:
        return TASK_STORE.load_task(task_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc


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
        project_topic=task.get("project_topic") or task.get("metadata", {}).get("project_topic"),
        model_provider=task.get("model_provider") or task.get("metadata", {}).get("model_provider"),
        artifacts=artifacts,
    )


def _to_detail(task: dict) -> TaskDetail:
    snapshot = _to_snapshot(task)
    return TaskDetail(
        **snapshot.model_dump(),
        run_root=task.get("run_root"),
        output_dir=task.get("output_dir"),
        records=task.get("records", []),
        markdown_preview=task.get("markdown_preview"),
    )


def _artifact_from_entry(key: str, payload: dict) -> TaskArtifact:
    return TaskArtifact(
        key=key,
        filename=payload["filename"],
        content_type=payload.get("content_type", "application/octet-stream"),
        size_bytes=payload.get("size_bytes"),
    )


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


def _collect_report_artifacts(result) -> dict:
    return {
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
