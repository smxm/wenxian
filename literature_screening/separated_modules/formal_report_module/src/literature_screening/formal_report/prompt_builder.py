from __future__ import annotations

import json
from pathlib import Path

from literature_screening.formal_report.models import LiteratureCard


def build_literature_card_prompt(
    template_path: Path,
    *,
    project_topic: str,
    paper_record: dict,
    screening_info: dict,
) -> str:
    template = template_path.read_text(encoding="utf-8")
    return (
        template.replace("{{ project_topic }}", project_topic)
        .replace("{{ paper_record }}", json.dumps(paper_record, ensure_ascii=False, indent=2))
        .replace("{{ screening_info }}", json.dumps(screening_info, ensure_ascii=False, indent=2))
        .replace("{{ output_schema }}", json.dumps(_literature_card_output_shape(), ensure_ascii=False, indent=2))
    )


def build_literature_card_batch_prompt(
    template_path: Path,
    *,
    project_topic: str,
    items: list[dict],
) -> str:
    template = template_path.read_text(encoding="utf-8")
    batch_shape = {
        "cards": [_literature_card_output_shape()],
    }
    return (
        template.replace("{{ project_topic }}", project_topic)
        .replace("{{ items }}", json.dumps(items, ensure_ascii=False, indent=2))
        .replace("{{ output_schema }}", json.dumps(batch_shape, ensure_ascii=False, indent=2))
    )


def build_formal_report_overview_prompt(
    template_path: Path,
    *,
    project_topic: str,
    report_title_hint: str,
    cards: list[LiteratureCard],
) -> str:
    template = template_path.read_text(encoding="utf-8")
    category_names = sorted({card.classification.primary_category for card in cards})
    payload = [_card_to_prompt_payload(card) for card in cards]

    return (
        template.replace("{{ project_topic }}", project_topic)
        .replace("{{ report_title_hint }}", report_title_hint)
        .replace("{{ category_names }}", ", ".join(category_names))
        .replace("{{ cards }}", json.dumps(payload, ensure_ascii=False, indent=2))
        .replace("{{ output_schema }}", json.dumps(_formal_report_overview_output_shape(), ensure_ascii=False, indent=2))
    )


def _card_to_prompt_payload(card: LiteratureCard) -> dict:
    return {
        "paper_id": card.paper_id,
        "title_en": card.source_record.title_en,
        "title_zh": card.source_record.title_zh,
        "year": card.source_record.year,
        "journal": card.source_record.journal,
        "one_sentence_summary": card.content_summary.one_sentence_summary,
        "core_summary": card.content_summary.core_summary,
        "research_focus": card.content_summary.research_focus,
        "value_for_topic": card.content_summary.value_for_topic,
        "limitations": card.content_summary.limitations,
        "primary_category": card.classification.primary_category,
        "secondary_category": card.classification.secondary_category,
        "study_type": card.classification.study_type,
        "application_context": card.classification.application_context,
        "core_problem": card.classification.core_problem,
        "method_keywords": card.classification.method_keywords,
        "domain_tags": card.classification.domain_tags,
        "recommended_level": card.reporting_flags.recommended_level,
        "is_key_paper": card.reporting_flags.is_key_paper,
    }


def _literature_card_output_shape() -> dict:
    return {
        "paper_id": "string",
        "source_record": {
            "title_en": "string",
            "title_zh": "string|null",
            "authors": ["string"],
            "year": "integer|null",
            "journal": "string|null",
            "doi": "string|null",
            "abstract": "string|null",
        },
        "screening_info": {
            "decision": "include|exclude|uncertain",
            "screen_stage": "string",
            "reason": "string",
            "confidence": "number(0-1)",
        },
        "content_summary": {
            "one_sentence_summary": "string",
            "core_summary": "string",
            "research_focus": "string",
            "value_for_topic": "string",
            "limitations": "string",
        },
        "classification": {
            "primary_category": "string",
            "secondary_category": "string|null",
            "study_type": "string",
            "application_context": "string|null",
            "core_problem": "string",
            "method_keywords": ["string"],
            "domain_tags": ["string"],
        },
        "reporting_flags": {
            "recommended_level": "high|medium|low",
            "is_key_paper": "boolean",
        },
    }


def _formal_report_overview_output_shape() -> dict:
    return {
        "report_title": "string",
        "overview": "string",
        "category_overviews": [
            {
                "category_name": "string",
                "category_summary": "string",
                "category_value": "string",
                "representative_paper_ids": ["paper_id"],
            }
        ],
        "conclusion": "string",
    }
