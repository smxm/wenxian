from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TaskKind = Literal["strategy", "screening", "report"]
TaskStatus = Literal["pending", "running", "succeeded", "failed", "cancelled"]
ProviderName = Literal["deepseek", "kimi"]
ReferenceStyle = Literal["gbt7714", "apa7"]
DatasetKind = Literal[
    "included",
    "excluded",
    "unused",
    "included_reviewed",
    "excluded_reviewed",
    "cumulative_included",
    "fulltext_ready",
    "report_source",
]
StrategyDatabase = Literal["scopus", "wos", "pubmed", "cnki"]
FulltextStatus = Literal["pending", "ready", "unavailable", "deferred"]


class ModelSettings(BaseModel):
    provider: ProviderName
    model_name: str
    api_base_url: str
    api_key_env: str
    api_key: str | None = None
    temperature: float = 0.0
    max_tokens: int = 1536
    min_request_interval_seconds: float = 2.0


class ScreeningTaskCreate(BaseModel):
    title: str
    topic: str
    inclusion: list[str]
    exclusion: list[str]
    model: ModelSettings
    batch_size: int = Field(default=10, ge=1, le=50)
    target_include_count: int = Field(default=9999, ge=1)
    stop_when_target_reached: bool = False
    allow_uncertain: bool = True
    retry_times: int = Field(default=6, ge=0, le=10)
    request_timeout_seconds: int = Field(default=240, ge=30, le=600)
    encoding: str = "auto"


class ReportTaskCreate(BaseModel):
    title: str
    screening_task_id: str | None = None
    dataset_ids: list[str] = Field(default_factory=list)
    project_topic: str
    model: ModelSettings
    report_name: str = "simple_report"
    retry_times: int = Field(default=6, ge=0, le=10)
    timeout_seconds: int = Field(default=240, ge=30, le=600)
    reference_style: ReferenceStyle = "gbt7714"


class StrategyTaskCreate(BaseModel):
    title: str
    project_id: str | None = None
    new_project_name: str = ""
    new_project_description: str = ""
    project_topic: str
    research_need: str
    selected_databases: list[StrategyDatabase] = Field(default_factory=lambda: ["scopus", "wos", "pubmed", "cnki"])
    model: ModelSettings
    retry_times: int = Field(default=4, ge=0, le=10)
    timeout_seconds: int = Field(default=180, ge=30, le=600)


class ProjectCreate(BaseModel):
    name: str
    topic: str
    description: str = ""


class ProjectUpdate(BaseModel):
    name: str
    topic: str
    description: str = ""


class DatasetRecord(BaseModel):
    id: str
    project_id: str
    task_id: str | None = None
    kind: DatasetKind | str
    label: str
    filename: str
    path: str
    format: str
    record_count: int | None = None
    source_dataset_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    metadata: dict = Field(default_factory=dict)


class FulltextQueueItem(BaseModel):
    paper_id: str
    title: str
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    doi_url: str | None = None
    landing_url: str | None = None
    pdf_url: str | None = None
    oa_status: str | None = None
    status: FulltextStatus = "pending"
    note: str = ""
    updated_at: datetime


class ProjectSnapshot(BaseModel):
    id: str
    name: str
    topic: str
    description: str = ""
    created_at: datetime
    updated_at: datetime
    dataset_count: int = 0


class ProjectDetail(ProjectSnapshot):
    tasks: list["TaskSnapshot"] = Field(default_factory=list)
    datasets: list[DatasetRecord] = Field(default_factory=list)
    fulltext_queue: list[FulltextQueueItem] = Field(default_factory=list)
    fulltext_source_dataset_ids: list[str] = Field(default_factory=list)


class TaskTemplateRecord(BaseModel):
    id: str
    project_id: str | None = None
    name: str
    scope: Literal["global", "project"] = "project"
    payload: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class TaskArtifact(BaseModel):
    key: str
    filename: str
    content_type: str = "application/octet-stream"
    size_bytes: int | None = None


class TaskEvent(BaseModel):
    id: str
    kind: str
    message: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


class ReviewOverrideRequest(BaseModel):
    paper_id: str
    decision: Literal["include", "exclude", "uncertain"]
    reason: str = ""


class BulkReviewOverrideRequest(BaseModel):
    entries_text: str
    decision: Literal["include", "exclude", "uncertain"] = "exclude"
    reason: str = ""


class ReferenceOverrideRequest(BaseModel):
    references_text: str


class FulltextQueueRebuildRequest(BaseModel):
    source_dataset_ids: list[str] = Field(default_factory=list)


class FulltextStatusUpdateRequest(BaseModel):
    paper_id: str
    status: FulltextStatus
    note: str = ""


class RetryTaskRequest(BaseModel):
    mode: Literal["retry", "resume"] = "resume"


class TaskSnapshot(BaseModel):
    id: str
    kind: TaskKind
    status: TaskStatus
    title: str
    phase: str
    created_at: datetime
    updated_at: datetime
    summary: dict | None = None
    error: str | None = None
    phase_label: str | None = None
    progress_current: int | None = None
    progress_total: int | None = None
    progress_message: str | None = None
    project_id: str | None = None
    parent_task_id: str | None = None
    input_dataset_ids: list[str] = Field(default_factory=list)
    output_dataset_ids: list[str] = Field(default_factory=list)
    project_topic: str | None = None
    model_provider: str | None = None
    attempt_count: int = 0
    artifacts: list[TaskArtifact] = Field(default_factory=list)


class StrategySearchBlock(BaseModel):
    database: StrategyDatabase
    title: str
    query: str | None = None
    lines: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class StrategyPlan(BaseModel):
    topic: str
    intent_summary: str
    screening_topic: str
    inclusion: list[str] = Field(default_factory=list)
    exclusion: list[str] = Field(default_factory=list)
    search_blocks: list[StrategySearchBlock] = Field(default_factory=list)
    caution_notes: list[str] = Field(default_factory=list)


class ScreeningRecordRow(BaseModel):
    paper_id: str
    title: str
    decision: str
    confidence: float | str | None = None
    reason: str
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    abstract: str | None = None


class TaskDetail(TaskSnapshot):
    run_root: str | None = None
    output_dir: str | None = None
    records: list[ScreeningRecordRow] = Field(default_factory=list)
    markdown_preview: str | None = None
    events: list[TaskEvent] = Field(default_factory=list)
    strategy_plan: StrategyPlan | None = None
    request_payload: dict | None = None


ProjectDetail.model_rebuild()

