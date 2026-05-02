from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


DecisionValue = Literal["include", "exclude", "uncertain"]
PaperStatus = Literal["unprocessed", "included", "excluded", "uncertain", "unused", "error"]
ReportFormat = Literal["md", "json"]
SummaryFormat = Literal["json"]


class ProjectConfig(BaseModel):
    name: str
    output_dir: str
    save_raw_response: bool = True
    save_intermediate_files: bool = True


class InputConfig(BaseModel):
    input_files: list[str]
    encoding: str = "utf-8"


class DedupConfig(BaseModel):
    enabled: bool = True
    strict_doi_match: bool = True
    normalized_title_exact_match: bool = True
    fuzzy_title_match: bool = False


class ScreeningConfig(BaseModel):
    batch_size: int = Field(default=10, ge=1, le=100)
    target_include_count: int = Field(ge=1)
    stop_when_target_reached: bool = True
    allow_uncertain: bool = True
    retry_times: int = Field(default=2, ge=0, le=10)
    request_timeout_seconds: int = Field(default=120, ge=10, le=600)


class CriteriaConfig(BaseModel):
    topic: str
    inclusion: list[str]
    exclusion: list[str]


class ModelConfig(BaseModel):
    provider: Literal["kimi", "deepseek"]
    model_name: str
    api_base_url: str
    api_key_env: str
    api_key: str | None = Field(default=None, exclude=True, repr=False)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=8192, ge=256, le=32768)
    min_request_interval_seconds: float = Field(default=0.0, ge=0, le=60)


class ReportConfig(BaseModel):
    export_included_ris: bool = True
    export_excluded_ris: bool = False
    export_unused_ris: bool = True
    export_included_bib: bool = False
    export_excluded_bib: bool = False
    export_unused_bib: bool = False
    included_report_format: ReportFormat = "md"
    excluded_report_format: ReportFormat = "md"
    summary_format: SummaryFormat = "json"


class RunConfig(BaseModel):
    project: ProjectConfig
    input: InputConfig
    dedup: DedupConfig = Field(default_factory=DedupConfig)
    screening: ScreeningConfig
    criteria: CriteriaConfig
    model: ModelConfig
    report: ReportConfig


class PaperRecord(BaseModel):
    paper_id: str
    entry_type: str | None = None
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None
    keywords: list[str] = Field(default_factory=list)
    normalized_title: str | None = None
    raw_bibtex: str | None = None
    source_files: list[str] = Field(default_factory=list)
    source_keys: list[str] = Field(default_factory=list)
    merged_from: list[str] = Field(default_factory=list)
    status: PaperStatus = "unprocessed"


class ScreeningDecision(BaseModel):
    paper_id: str
    batch_id: str
    decision: DecisionValue
    reason: str
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    screen_stage: str = "title_abstract"
    model_provider: str
    model_name: str
    timestamp: datetime


class BatchRequestRecord(BaseModel):
    batch_id: str
    paper_ids: list[str]
    paper_count: int
    criteria_snapshot: dict[str, object]
    model_provider: str
    model_name: str
    created_at: datetime


class RunSummary(BaseModel):
    run_id: str
    input_files_count: int = 0
    raw_entries_count: int = 0
    deduped_entries_count: int = 0
    processed_count: int = 0
    included_count: int = 0
    excluded_count: int = 0
    uncertain_count: int = 0
    unused_count: int = 0
    batch_count: int = 0
    api_call_count: int = 0
    stop_reason: str
    started_at: datetime
    finished_at: datetime
