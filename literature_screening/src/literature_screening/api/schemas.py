from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TaskKind = Literal["screening", "report"]
TaskStatus = Literal["pending", "running", "succeeded", "failed"]
ProviderName = Literal["deepseek", "kimi"]
ReferenceStyle = Literal["gbt7714", "apa7"]


class ModelSettings(BaseModel):
    provider: ProviderName
    model_name: str
    api_base_url: str
    api_key_env: str
    temperature: float = 0.0
    max_tokens: int = 1536
    min_request_interval_seconds: float = 2.0


class ScreeningTaskCreate(BaseModel):
    title: str
    topic: str
    inclusion: list[str]
    exclusion: list[str]
    model: ModelSettings
    batch_size: int = Field(default=20, ge=1, le=50)
    target_include_count: int = Field(default=9999, ge=1)
    stop_when_target_reached: bool = False
    allow_uncertain: bool = True
    retry_times: int = Field(default=6, ge=0, le=10)
    request_timeout_seconds: int = Field(default=240, ge=30, le=600)
    encoding: str = "auto"


class ReportTaskCreate(BaseModel):
    title: str
    screening_task_id: str
    project_topic: str
    model: ModelSettings
    report_name: str = "simple_report"
    retry_times: int = Field(default=6, ge=0, le=10)
    timeout_seconds: int = Field(default=240, ge=30, le=600)
    reference_style: ReferenceStyle = "gbt7714"


class TaskArtifact(BaseModel):
    key: str
    filename: str
    content_type: str = "application/octet-stream"
    size_bytes: int | None = None


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
    project_topic: str | None = None
    model_provider: str | None = None
    artifacts: list[TaskArtifact] = Field(default_factory=list)


class ScreeningRecordRow(BaseModel):
    paper_id: str
    title: str
    decision: str
    confidence: float | str | None = None
    reason: str
    year: int | None = None
    journal: str | None = None
    doi: str | None = None


class TaskDetail(TaskSnapshot):
    run_root: str | None = None
    output_dir: str | None = None
    records: list[ScreeningRecordRow] = Field(default_factory=list)
    markdown_preview: str | None = None

