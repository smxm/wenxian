from __future__ import annotations

from pathlib import Path

from literature_screening.core.models import PaperRecord
from literature_screening.core.models import ScreeningDecision
from literature_screening.formal_report.models import LiteratureCard
from literature_screening.formal_report.models import ReportOverviewPayload
from literature_screening.formal_report.prompt_builder import build_literature_card_batch_prompt
from literature_screening.formal_report.prompt_builder import build_formal_report_overview_prompt
from literature_screening.formal_report.prompt_builder import build_literature_card_prompt
from literature_screening.formal_report.validator import validate_formal_report_overview
from literature_screening.formal_report.validator import validate_literature_card
from literature_screening.screening.llm_client import ChatCompletionClient
from literature_screening.screening.response_parser import parse_model_json


def generate_literature_card(
    client: ChatCompletionClient,
    *,
    template_path: Path,
    project_topic: str,
    paper: PaperRecord,
    decision: ScreeningDecision,
    raw_output_path: Path | None = None,
) -> LiteratureCard:
    paper_record = {
        "paper_id": paper.paper_id,
        "title": paper.title,
        "authors": paper.authors,
        "year": paper.year,
        "journal": paper.journal,
        "doi": paper.doi,
        "abstract": _truncate_text(paper.abstract, 1600),
        "keywords": paper.keywords,
    }
    screening_info = {
        "decision": decision.decision,
        "screen_stage": decision.screen_stage,
        "reason": decision.reason,
        "confidence": decision.confidence,
    }

    prompt = build_literature_card_prompt(
        template_path,
        project_topic=project_topic,
        paper_record=paper_record,
        screening_info=screening_info,
    )
    raw_text = client.chat(prompt)
    if raw_output_path is not None:
        raw_output_path.write_text(raw_text, encoding="utf-8")
    payload = parse_model_json(raw_text)
    validate_literature_card(payload)
    return LiteratureCard.model_validate(payload)


def generate_report_overview(
    client: ChatCompletionClient,
    *,
    template_path: Path,
    project_topic: str,
    report_title_hint: str,
    cards: list[LiteratureCard],
    raw_output_path: Path | None = None,
) -> ReportOverviewPayload:
    prompt = build_formal_report_overview_prompt(
        template_path,
        project_topic=project_topic,
        report_title_hint=report_title_hint,
        cards=cards,
    )
    raw_text = client.chat(prompt)
    if raw_output_path is not None:
        raw_output_path.write_text(raw_text, encoding="utf-8")
    payload = parse_model_json(raw_text)
    validate_formal_report_overview(
        payload,
        expected_categories=sorted({card.classification.primary_category for card in cards}),
        available_paper_ids=[card.paper_id for card in cards],
    )
    return ReportOverviewPayload.model_validate(payload)


def generate_literature_card_batch(
    client: ChatCompletionClient,
    *,
    template_path: Path,
    project_topic: str,
    items: list[tuple[PaperRecord, ScreeningDecision]],
    raw_output_path: Path | None = None,
) -> list[LiteratureCard]:
    prompt_items = []
    expected_paper_ids: list[str] = []

    for paper, decision in items:
        prompt_items.append(
            {
                "paper_record": {
                    "paper_id": paper.paper_id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "year": paper.year,
                    "journal": paper.journal,
                    "doi": paper.doi,
                    "abstract": _truncate_text(paper.abstract, 1600),
                    "keywords": paper.keywords,
                },
                "screening_info": {
                    "decision": decision.decision,
                    "screen_stage": decision.screen_stage,
                    "reason": decision.reason,
                    "confidence": decision.confidence,
                },
            }
        )
        expected_paper_ids.append(paper.paper_id)

    prompt = build_literature_card_batch_prompt(
        template_path,
        project_topic=project_topic,
        items=prompt_items,
    )
    raw_text = client.chat(prompt)
    if raw_output_path is not None:
        raw_output_path.write_text(raw_text, encoding="utf-8")
    payload = parse_model_json(raw_text)
    cards_payload = payload.get("cards")
    if not isinstance(cards_payload, list):
        raise ValueError("Literature card batch response must contain a 'cards' list.")

    cards = [LiteratureCard.model_validate(item) for item in cards_payload]
    for card_payload in cards_payload:
        validate_literature_card(card_payload)

    returned_ids = [card.paper_id for card in cards]
    if returned_ids != expected_paper_ids:
        raise ValueError(
            f"Literature card batch paper_id order mismatch: expected {expected_paper_ids}, got {returned_ids}."
        )
    return cards


def _truncate_text(value: str | None, max_length: int) -> str | None:
    if value is None or len(value) <= max_length:
        return value
    return value[: max_length - 3].rstrip() + "..."
