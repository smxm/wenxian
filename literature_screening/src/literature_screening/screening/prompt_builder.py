from __future__ import annotations

import json
from pathlib import Path

from literature_screening.core.models import CriteriaConfig, PaperRecord
from literature_screening.core.schema import BATCH_SCREENING_RESPONSE_SCHEMA


def build_screening_prompt(
    template_path: Path,
    batch_id: str,
    criteria: CriteriaConfig,
    papers: list[PaperRecord],
    min_include_confidence: float = 0.8,
    allow_uncertain: bool = True,
) -> str:
    template = template_path.read_text(encoding="utf-8")
    paper_lines = [_format_paper_block(index=index, paper=paper) for index, paper in enumerate(papers, start=1)]
    normalized_threshold = max(0.0, min(1.0, min_include_confidence))
    below_threshold_instruction = (
        "判为 `uncertain`，保留给人工复核"
        if allow_uncertain
        else "判为 `exclude`，并在 reason 中说明相关度未达到纳入阈值"
    )

    return (
        template.replace("{{ topic }}", criteria.topic)
        .replace("{{ inclusion }}", "\n".join(f"- {item}" for item in criteria.inclusion))
        .replace("{{ exclusion }}", "\n".join(f"- {item}" for item in criteria.exclusion))
        .replace("{{ min_include_confidence }}", f"{normalized_threshold:.2f}")
        .replace("{{ min_include_confidence_percent }}", f"{round(normalized_threshold * 100)}%")
        .replace("{{ below_threshold_instruction }}", below_threshold_instruction)
        .replace("{{ batch_id }}", batch_id)
        .replace("{{ paper_count }}", str(len(papers)))
        .replace("{{ paper_ids }}", ", ".join(paper.paper_id for paper in papers))
        .replace("{{ papers }}", "\n".join(paper_lines))
        .replace("{{ output_schema }}", json.dumps(BATCH_SCREENING_RESPONSE_SCHEMA, ensure_ascii=False, indent=2))
    )


def _format_paper_block(index: int, paper: PaperRecord) -> str:
    payload = {
        "paper_id": paper.paper_id,
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "journal": paper.journal,
        "doi": paper.doi,
        "abstract": paper.abstract if paper.abstract else "[ABSTRACT_MISSING]",
        "keywords": paper.keywords if paper.keywords else ["[KEYWORDS_MISSING]"],
    }

    return (
        f"[Paper {index}]\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n"
    )
