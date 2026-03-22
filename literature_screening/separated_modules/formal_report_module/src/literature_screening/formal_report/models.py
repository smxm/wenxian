from __future__ import annotations

from pydantic import BaseModel, Field


DecisionValue = str
RecommendedLevel = str


class SourceRecord(BaseModel):
    title_en: str
    title_zh: str | None = None
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    abstract: str | None = None


class CardScreeningInfo(BaseModel):
    decision: str
    screen_stage: str
    reason: str
    confidence: float = Field(ge=0, le=1)


class ContentSummary(BaseModel):
    one_sentence_summary: str
    core_summary: str
    research_focus: str
    value_for_topic: str
    limitations: str


class ClassificationInfo(BaseModel):
    primary_category: str
    secondary_category: str | None = None
    study_type: str
    application_context: str | None = None
    core_problem: str
    method_keywords: list[str] = Field(default_factory=list)
    domain_tags: list[str] = Field(default_factory=list)


class ReportingFlags(BaseModel):
    recommended_level: str
    is_key_paper: bool


class LiteratureCard(BaseModel):
    paper_id: str
    source_record: SourceRecord
    screening_info: CardScreeningInfo
    content_summary: ContentSummary
    classification: ClassificationInfo
    reporting_flags: ReportingFlags


class CategoryOverview(BaseModel):
    category_name: str
    category_summary: str
    category_value: str
    representative_paper_ids: list[str] = Field(default_factory=list)


class ReportOverviewPayload(BaseModel):
    report_title: str
    overview: str
    category_overviews: list[CategoryOverview] = Field(default_factory=list)
    conclusion: str

