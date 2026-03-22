from __future__ import annotations

import json
import time
from pathlib import Path

from literature_screening.core.models import ModelConfig
from literature_screening.core.models import PaperRecord
from literature_screening.core.models import ScreeningDecision
from literature_screening.formal_report.fallback import build_fallback_literature_cards
from literature_screening.formal_report.fallback import build_fallback_report_overview
from literature_screening.formal_report.generator import generate_report_overview
from literature_screening.formal_report.generator import generate_literature_card_batch
from literature_screening.formal_report.models import LiteratureCard
from literature_screening.formal_report.models import ReportOverviewPayload
from literature_screening.formal_report.renderer import render_formal_report_markdown
from literature_screening.screening.llm_client import ChatCompletionClient


def load_included_rows(screening_output_dir: Path) -> list[tuple[PaperRecord, ScreeningDecision]]:
    deduped_payload = json.loads((screening_output_dir / "deduped_records.json").read_text(encoding="utf-8"))
    decisions_payload = json.loads((screening_output_dir / "screening_decisions.json").read_text(encoding="utf-8"))

    papers = [PaperRecord.model_validate(item) for item in deduped_payload]
    decisions = [ScreeningDecision.model_validate(item) for item in decisions_payload]
    paper_map = {paper.paper_id: paper for paper in papers}

    included_rows: list[tuple[PaperRecord, ScreeningDecision]] = []
    for decision in decisions:
        if decision.decision != "include":
            continue
        paper = paper_map.get(decision.paper_id)
        if paper is not None:
            included_rows.append((paper, decision))
    return included_rows


def generate_formal_report_from_screening(
    *,
    screening_output_dir: Path,
    report_output_dir: Path,
    project_topic: str,
    report_title_hint: str,
    model_config: ModelConfig | None = None,
    timeout_seconds: int = 180,
    retry_times: int = 4,
    card_batch_size: int = 3,
) -> None:
    report_output_dir.mkdir(parents=True, exist_ok=True)
    (report_output_dir / "logs").mkdir(exist_ok=True)
    (report_output_dir / "raw").mkdir(exist_ok=True)

    included_rows = load_included_rows(screening_output_dir)

    cards = build_fallback_literature_cards(included_rows)
    client = ChatCompletionClient(model_config, timeout_seconds=timeout_seconds) if model_config is not None else None
    if client is not None:
        cards = _try_llm_cards(
            client=client,
            included_rows=included_rows,
            report_output_dir=report_output_dir,
            project_topic=project_topic,
            retry_times=retry_times,
            batch_size=card_batch_size,
        )

    write_cards(cards, report_output_dir / "literature_cards.json")

    overview = build_fallback_report_overview(cards, project_topic)
    if client is not None:
        overview = _try_llm_overview(
            client=client,
            cards=cards,
            report_output_dir=report_output_dir,
            project_topic=project_topic,
            report_title_hint=report_title_hint,
            retry_times=retry_times,
            fallback_overview=overview,
        )

    (report_output_dir / "formal_report_overview.json").write_text(
        json.dumps(overview.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    render_formal_report_markdown(overview, cards, report_output_dir / "formal_report.md")


def write_cards(cards: list[LiteratureCard], output_path: Path) -> None:
    output_path.write_text(
        json.dumps([card.model_dump(mode="json") for card in cards], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _try_llm_cards(
    *,
    client: ChatCompletionClient,
    included_rows: list[tuple[PaperRecord, ScreeningDecision]],
    report_output_dir: Path,
    project_topic: str,
    retry_times: int,
    batch_size: int,
) -> list[LiteratureCard]:
    template_path = Path(__file__).resolve().parents[3] / "prompts" / "literature_card_batch_prompt.md"
    cards_by_id = _load_existing_cards(report_output_dir / "literature_cards.json")

    for batch_index in range(0, len(included_rows), batch_size):
        batch_rows = included_rows[batch_index : batch_index + batch_size]
        expected_ids = [paper.paper_id for paper, _ in batch_rows]
        if all(paper_id in cards_by_id for paper_id in expected_ids):
            continue

        raw_output_path = report_output_dir / "raw" / f"cards_batch_{(batch_index // batch_size) + 1:03d}.txt"
        try:
            cards = _request_card_batch_with_retries(
                client=client,
                template_path=template_path,
                project_topic=project_topic,
                items=batch_rows,
                raw_output_path=raw_output_path,
                retry_times=retry_times,
            )
        except Exception as exc:
            _append_log(report_output_dir / "logs" / "card_generation_errors.log", f"{expected_ids}: {exc}")
            cards = build_fallback_literature_cards(batch_rows)

        for card in cards:
            cards_by_id[card.paper_id] = card
        write_cards(
            [cards_by_id[paper.paper_id] for paper, _ in included_rows if paper.paper_id in cards_by_id],
            report_output_dir / "literature_cards.json",
        )

    return [cards_by_id[paper.paper_id] for paper, _ in included_rows]


def _try_llm_overview(
    *,
    client: ChatCompletionClient,
    cards: list[LiteratureCard],
    report_output_dir: Path,
    project_topic: str,
    report_title_hint: str,
    retry_times: int,
    fallback_overview: ReportOverviewPayload,
) -> ReportOverviewPayload:
    template_path = Path(__file__).resolve().parents[3] / "prompts" / "formal_report_overview_prompt.md"
    raw_output_path = report_output_dir / "raw" / "formal_report_overview.txt"

    for attempt in range(retry_times + 1):
        try:
            return generate_report_overview(
                client=client,
                template_path=template_path,
                project_topic=project_topic,
                report_title_hint=report_title_hint,
                cards=cards,
                raw_output_path=raw_output_path,
            )
        except Exception as exc:
            _append_log(report_output_dir / "logs" / "overview_generation_errors.log", f"attempt {attempt + 1}: {exc}")
            if attempt < retry_times:
                delay_seconds = client.extract_retry_after_seconds(exc) or (2 ** attempt)
                time.sleep(delay_seconds)

    return fallback_overview


def _request_card_batch_with_retries(
    *,
    client: ChatCompletionClient,
    template_path: Path,
    project_topic: str,
    items: list[tuple[PaperRecord, ScreeningDecision]],
    raw_output_path: Path,
    retry_times: int,
) -> list[LiteratureCard]:
    last_error: Exception | None = None
    for attempt in range(retry_times + 1):
        try:
            return generate_literature_card_batch(
                client=client,
                template_path=template_path,
                project_topic=project_topic,
                items=items,
                raw_output_path=raw_output_path,
            )
        except Exception as exc:
            last_error = exc
            if attempt < retry_times:
                delay_seconds = client.extract_retry_after_seconds(exc) or (2 ** attempt)
                time.sleep(delay_seconds)
    assert last_error is not None
    raise last_error


def _load_existing_cards(path: Path) -> dict[str, LiteratureCard]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    cards = [LiteratureCard.model_validate(item) for item in payload]
    return {card.paper_id: card for card in cards}


def _append_log(path: Path, message: str) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(message.rstrip() + "\n")
