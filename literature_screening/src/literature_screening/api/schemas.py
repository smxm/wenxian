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
FulltextStatus = Literal["pending", "ready", "excluded", "unavailable", "deferred"]
WorkbenchAccessStatus = Literal["pending", "ready", "unavailable", "deferred"]
WorkbenchFinalDecision = Literal["undecided", "include", "exclude", "deferred"]
WorkbenchStage = Literal[
    "needs-screening",
    "screened-out",
    "needs-link",
    "needs-access",
    "ready-for-decision",
    "report-included",
    "report-excluded",
    "unavailable",
    "deferred",
]


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
    target_include_count: int | None = Field(default=None, ge=1)
    stop_when_target_reached: bool = False
    allow_uncertain: bool = True
    retry_times: int = Field(default=6, ge=0, le=10)
    request_timeout_seconds: int = Field(default=240, ge=30, le=600)
    encoding: str = "auto"


class ReportTaskCreate(BaseModel):
    title: str
    project_id: str | None = None
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
    project_topic: str = ""
    research_need: str
    selected_databases: list[StrategyDatabase] = Field(default_factory=lambda: ["scopus", "wos", "pubmed", "cnki"])
    model: ModelSettings
    retry_times: int = Field(default=4, ge=0, le=10)
    timeout_seconds: int = Field(default=180, ge=30, le=600)


class ThreadPrefillRequest(BaseModel):
    research_need: str
    selected_databases: list[StrategyDatabase] = Field(default_factory=lambda: ["scopus", "wos", "pubmed", "cnki"])
    model: ModelSettings
    timeout_seconds: int = Field(default=180, ge=30, le=600)


class ProjectCreate(BaseModel):
    name: str
    topic: str
    description: str = ""


class ProjectUpdate(BaseModel):
    name: str
    topic: str
    description: str = ""


class ThreadStrategySettings(BaseModel):
    research_need: str = ""
    selected_databases: list[StrategyDatabase] = Field(default_factory=lambda: ["scopus", "wos", "pubmed", "cnki"])
    model: ModelSettings | None = None
    latest_task_id: str | None = None
    plan: StrategyPlan | None = None


class ThreadScreeningSettings(BaseModel):
    topic: str = ""
    criteria_markdown: str = ""
    inclusion: list[str] = Field(default_factory=list)
    exclusion: list[str] = Field(default_factory=list)
    model: ModelSettings | None = None
    batch_size: int = Field(default=10, ge=1, le=50)
    target_include_count: int | None = Field(default=None, ge=1)
    stop_when_target_reached: bool = False
    allow_uncertain: bool = True
    retry_times: int = Field(default=6, ge=0, le=10)
    request_timeout_seconds: int = Field(default=240, ge=30, le=600)
    encoding: str = "auto"


class ThreadProfile(BaseModel):
    strategy: ThreadStrategySettings = Field(default_factory=ThreadStrategySettings)
    screening: ThreadScreeningSettings = Field(default_factory=ThreadScreeningSettings)
    last_updated_at: datetime | None = None


class ProjectWorkflowUpdate(BaseModel):
    name: str | None = None
    topic: str | None = None
    description: str | None = None
    thread_profile: ThreadProfile


class DatasetRecord(BaseModel):
    id: str
    project_id: str
    task_id: str | None = None
    kind: DatasetKind | str
    label: str
    filename: str
    path: str
    relative_path: str | None = None
    format: str
    record_count: int | None = None
    source_dataset_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    metadata: dict = Field(default_factory=dict)


class FulltextQueueItem(BaseModel):
    paper_id: str
    candidate_id: str | None = None
    title: str
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    confidence: float | str | None = None
    screening_decision: str | None = None
    screening_reason: str = ""
    doi_url: str | None = None
    landing_url: str | None = None
    pdf_url: str | None = None
    oa_status: str | None = None
    status: FulltextStatus = "pending"
    note: str = ""
    updated_at: datetime


class WorkbenchLink(BaseModel):
    kind: str
    label: str
    url: str
    source: str
    primary: bool = False


class WorkbenchScreeningEvent(BaseModel):
    task_id: str
    task_title: str | None = None
    round_index: int | None = None
    paper_id: str
    decision: str
    reason: str = ""
    confidence: float | str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    latest: bool = False


class WorkbenchSourceRecordRef(BaseModel):
    paper_id: str
    task_id: str | None = None
    dataset_id: str | None = None
    dataset_label: str | None = None


class WorkbenchCandidateItem(BaseModel):
    candidate_id: str
    fingerprint: str
    title: str
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    source_url: str | None = None
    language: str = "unknown"
    latest_screening_decision: str | None = None
    latest_screening_reason: str = ""
    latest_screening_confidence: float | str | None = None
    access_status: WorkbenchAccessStatus = "pending"
    final_decision: WorkbenchFinalDecision = "undecided"
    stage: WorkbenchStage
    access_note: str = ""
    final_note: str = ""
    oa_status: str | None = None
    preferred_open_url: str | None = None
    preferred_pdf_url: str | None = None
    links: list[WorkbenchLink] = Field(default_factory=list)
    screening_history: list[WorkbenchScreeningEvent] = Field(default_factory=list)
    source_record_refs: list[WorkbenchSourceRecordRef] = Field(default_factory=list)
    source_dataset_ids: list[str] = Field(default_factory=list)
    source_dataset_labels: list[str] = Field(default_factory=list)
    source_task_ids: list[str] = Field(default_factory=list)
    source_round_labels: list[str] = Field(default_factory=list)
    updated_at: datetime


class WorkbenchSummary(BaseModel):
    total_candidates: int = 0
    actionable_candidates: int = 0
    needs_screening: int = 0
    screened_out: int = 0
    needs_link: int = 0
    needs_access: int = 0
    ready_for_decision: int = 0
    report_included: int = 0
    report_excluded: int = 0
    unavailable: int = 0
    deferred: int = 0


class ProjectWorkbench(BaseModel):
    source_dataset_ids: list[str] = Field(default_factory=list)
    generated_at: datetime | None = None
    summary: WorkbenchSummary = Field(default_factory=WorkbenchSummary)
    items: list[WorkbenchCandidateItem] = Field(default_factory=list)


class ProjectSnapshot(BaseModel):
    id: str
    name: str
    topic: str
    description: str = ""
    thread_profile: ThreadProfile | None = None
    created_at: datetime
    updated_at: datetime
    dataset_count: int = 0


class ProjectDetail(ProjectSnapshot):
    tasks: list["TaskSnapshot"] = Field(default_factory=list)
    datasets: list[DatasetRecord] = Field(default_factory=list)
    workbench: ProjectWorkbench = Field(default_factory=ProjectWorkbench)
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


class SelectionReviewOverrideRequest(BaseModel):
    paper_ids: list[str] = Field(default_factory=list)
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


class FulltextBatchStatusUpdateRequest(BaseModel):
    paper_ids: list[str] = Field(default_factory=list)
    status: FulltextStatus
    note: str | None = None


class WorkbenchRebuildRequest(BaseModel):
    source_dataset_ids: list[str] = Field(default_factory=list)


class WorkbenchItemPatchRequest(BaseModel):
    access_status: WorkbenchAccessStatus | None = None
    final_decision: WorkbenchFinalDecision | None = None
    access_note: str | None = None
    final_note: str | None = None
    preferred_open_url: str | None = None
    preferred_pdf_url: str | None = None


class WorkbenchBatchPatchRequest(BaseModel):
    candidate_ids: list[str] = Field(default_factory=list)
    access_status: WorkbenchAccessStatus | None = None
    final_decision: WorkbenchFinalDecision | None = None
    access_note: str | None = None
    final_note: str | None = None


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


class ThreadPrefillResponse(BaseModel):
    strategy_plan: StrategyPlan
    criteria_markdown: str


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
    run_root_relative: str | None = None
    output_dir: str | None = None
    output_dir_relative: str | None = None
    records: list[ScreeningRecordRow] = Field(default_factory=list)
    markdown_preview: str | None = None
    events: list[TaskEvent] = Field(default_factory=list)
    strategy_plan: StrategyPlan | None = None
    request_payload: dict | None = None


ProjectDetail.model_rebuild()
