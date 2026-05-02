from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


StrategyDatabase = Literal["scopus", "wos", "pubmed", "cnki"]


class SearchStrategyBlock(BaseModel):
    database: StrategyDatabase
    title: str
    query: str | None = None
    lines: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class SearchStrategyPlan(BaseModel):
    topic: str
    intent_summary: str
    screening_topic: str
    inclusion: list[str] = Field(default_factory=list)
    exclusion: list[str] = Field(default_factory=list)
    search_blocks: list[SearchStrategyBlock] = Field(default_factory=list)
    caution_notes: list[str] = Field(default_factory=list)

