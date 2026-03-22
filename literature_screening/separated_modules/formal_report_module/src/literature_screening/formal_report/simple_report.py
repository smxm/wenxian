from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable

from pydantic import BaseModel

from literature_screening.core.models import ModelConfig
from literature_screening.core.models import PaperRecord
from literature_screening.core.models import ScreeningDecision
from literature_screening.formal_report.fallback import build_fallback_literature_cards
from literature_screening.formal_report.pipeline import load_included_rows
from literature_screening.formal_report.reference_list import ReferenceStyle
from literature_screening.formal_report.reference_list import build_reference_block
from literature_screening.formal_report.text_utils import normalize_text
from literature_screening.screening.llm_client import ChatCompletionClient
from literature_screening.screening.response_parser import parse_model_json

DEFAULT_SIMPLE_REPORT_FILENAME = "literature_report.md"
LEGACY_SIMPLE_REPORT_FILENAME = "simple_report.md"
ProgressCallback = Callable[[str, str, int | None, int | None, str | None], None]


class SimplePaperNote(BaseModel):
    paper_id: str
    title: str
    category: str
    summary: str
    analysis: str


def generate_simple_report(
    *,
    screening_output_dir: Path,
    report_output_dir: Path,
    project_topic: str,
    model_config: ModelConfig,
    timeout_seconds: int = 180,
    retry_times: int = 6,
    reference_style: ReferenceStyle = "gbt7714",
    max_papers: int | None = None,
    progress_callback: ProgressCallback | None = None,
) -> None:
    """Generate the detached report module's default concise literature report."""
    report_output_dir.mkdir(parents=True, exist_ok=True)
    (report_output_dir / "logs").mkdir(exist_ok=True)
    (report_output_dir / "raw").mkdir(exist_ok=True)

    included_rows = load_included_rows(screening_output_dir)
    if max_papers is not None:
        included_rows = included_rows[:max_papers]
    _emit_progress(
        progress_callback,
        "loading-notes",
        "Loading included papers",
        0,
        len(included_rows),
        f"Loaded {len(included_rows)} included papers",
    )
    cards = build_fallback_literature_cards(included_rows)
    card_map = {card.paper_id: card for card in cards}

    client = ChatCompletionClient(model_config, timeout_seconds=timeout_seconds)
    notes = _load_existing_notes(report_output_dir / "paper_notes.json")
    prompt_path = Path(__file__).resolve().parents[3] / "prompts" / "simple_paper_note_prompt.md"

    for paper, decision in included_rows:
        if paper.paper_id in notes:
            continue

        category = card_map[paper.paper_id].classification.primary_category
        completed = len(notes)
        _emit_progress(
            progress_callback,
            "building-paper-notes",
            "Building paper notes",
            completed,
            len(included_rows),
            f"Generating note for {paper.title}",
        )
        try:
            note = _request_note_with_retries(
                client=client,
                prompt_path=prompt_path,
                paper=paper,
                decision=decision,
                category=category,
                project_topic=project_topic,
                raw_output_path=report_output_dir / "raw" / f"{paper.paper_id}.txt",
                retry_times=retry_times,
            )
        except Exception as exc:
            _append_log(report_output_dir / "logs" / "paper_note_errors.log", f"{paper.paper_id}: {exc}")
            note = _fallback_note(paper=paper, decision=decision, category=category, project_topic=project_topic)

        notes[note.paper_id] = note
        _write_notes([notes[paper_id] for paper_id in notes], report_output_dir / "paper_notes.json")

    ordered_notes = [notes[paper.paper_id] for paper, _ in included_rows]
    ordered_papers = [paper for paper, _ in included_rows]
    _emit_progress(
        progress_callback,
        "building-references",
        "Building references",
        len(ordered_notes),
        len(ordered_notes),
        f"Rendering {reference_style.upper()} reference list",
    )
    reference_lines = build_reference_block(
        ordered_papers,
        style=reference_style,
        working_dir=report_output_dir / "raw" / "references",
    )
    _emit_progress(
        progress_callback,
        "rendering-report",
        "Rendering report",
        len(ordered_notes),
        len(ordered_notes),
        "Writing literature report markdown",
    )
    markdown = render_simple_report_markdown(
        project_topic=project_topic,
        notes=ordered_notes,
        records=ordered_papers,
        reference_style=reference_style,
        reference_lines=reference_lines,
    )
    (report_output_dir / DEFAULT_SIMPLE_REPORT_FILENAME).write_text(markdown, encoding="utf-8")
    (report_output_dir / LEGACY_SIMPLE_REPORT_FILENAME).write_text(markdown, encoding="utf-8")
    _emit_progress(
        progress_callback,
        "completed",
        "Completed",
        len(ordered_notes),
        len(ordered_notes),
        "Report generation completed",
    )


def render_simple_report_markdown(
    *,
    project_topic: str,
    notes: list[SimplePaperNote],
    records: list[PaperRecord] | None = None,
    reference_style: ReferenceStyle = "gbt7714",
    reference_lines: list[str] | None = None,
) -> str:
    grouped: dict[str, list[SimplePaperNote]] = {}
    for note in notes:
        grouped.setdefault(note.category, []).append(note)

    ordered_groups = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    total_summary = _build_total_summary(project_topic=project_topic, ordered_groups=ordered_groups)

    lines = ["# 一、相关文献总体情况", "", total_summary, ""]

    lines.extend(["# 二、类型划分", ""])
    for category_name, items in ordered_groups:
        lines.append(f"## {category_name}")
        lines.append("")
        lines.append(_build_category_intro(category_name=category_name, count=len(items), project_topic=project_topic))
        lines.append("")
        for note in items:
            lines.append(f"- {note.title}")
        lines.append("")

    lines.extend(["# 三、逐篇文献总结分析", ""])
    for note in notes:
        lines.append(f"## {note.title}")
        lines.append("")
        lines.append("总结：")
        lines.append(note.summary.strip())
        lines.append("")
        lines.append("分析：")
        lines.append(note.analysis.strip())
        lines.append("")

    lines.extend(["# 参考列表", ""])
    for item in (reference_lines or build_reference_block(records or [], style=reference_style)):
        lines.append(item)
    if records:
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _request_note_with_retries(
    *,
    client: ChatCompletionClient,
    prompt_path: Path,
    paper: PaperRecord,
    decision: ScreeningDecision,
    category: str,
    project_topic: str,
    raw_output_path: Path,
    retry_times: int,
) -> SimplePaperNote:
    last_error: Exception | None = None
    for attempt in range(retry_times + 1):
        try:
            prompt = _build_note_prompt(
                prompt_path=prompt_path,
                paper=paper,
                decision=decision,
                category=category,
                project_topic=project_topic,
            )
            raw_text = client.chat(prompt)
            raw_output_path.write_text(raw_text, encoding="utf-8")
            payload = parse_model_json(raw_text)
            return SimplePaperNote.model_validate(
                {
                    "paper_id": paper.paper_id,
                    "title": normalize_text(paper.title) or paper.title,
                    "category": category,
                    "summary": payload["summary"],
                    "analysis": payload["analysis"],
                }
            )
        except Exception as exc:
            last_error = exc
            if attempt < retry_times:
                delay_seconds = client.extract_retry_after_seconds(exc) or (2 ** attempt)
                time.sleep(delay_seconds)
    assert last_error is not None
    raise last_error


def _build_note_prompt(
    *,
    prompt_path: Path,
    paper: PaperRecord,
    decision: ScreeningDecision,
    category: str,
    project_topic: str,
) -> str:
    template = prompt_path.read_text(encoding="utf-8")
    payload = {
        "paper_id": paper.paper_id,
        "title": normalize_text(paper.title),
        "authors": paper.authors,
        "year": paper.year,
        "journal": normalize_text(paper.journal),
        "doi": paper.doi,
        "abstract": normalize_text(paper.abstract),
        "keywords": paper.keywords,
        "screening_reason": normalize_text(decision.reason),
        "category": category,
        "project_topic": project_topic,
    }
    schema = {
        "summary": "string",
        "analysis": "string",
    }
    return (
        template.replace("{{ input_payload }}", json.dumps(payload, ensure_ascii=False, indent=2))
        .replace("{{ output_schema }}", json.dumps(schema, ensure_ascii=False, indent=2))
    )


def _fallback_note(
    *,
    paper: PaperRecord,
    decision: ScreeningDecision,
    category: str,
    project_topic: str,
) -> SimplePaperNote:
    title = normalize_text(paper.title) or paper.title
    summary = _fallback_summary(title=title, abstract=normalize_text(paper.abstract), category=category)
    analysis = _fallback_analysis(reason=normalize_text(decision.reason), category=category, project_topic=project_topic)
    return SimplePaperNote(
        paper_id=paper.paper_id,
        title=title,
        category=category,
        summary=summary,
        analysis=analysis,
    )


def _fallback_summary(*, title: str, abstract: str | None, category: str) -> str:
    if abstract:
        first_sentence = abstract.split(". ")[0].split("。")[0].strip()
        if first_sentence:
            return f"该文献围绕“{title}”所对应的问题展开，主要属于{category}方向。摘要显示，研究重点涉及{_trim(first_sentence)}。"
    return f"该文献主要围绕“{title}”展开，可归入{category}方向，具体技术细节仍需结合全文进一步确认。"


def _fallback_analysis(*, reason: str | None, category: str, project_topic: str) -> str:
    if reason:
        return f"从当前主题“{project_topic}”来看，这篇文献的参考价值主要在于：{reason}"
    return f"对于“{project_topic}”这一主题，这篇文献可作为{category}方向的参考材料，用于补充相关机制、应用场景或系统设计思路。"


def _build_total_summary(*, project_topic: str, ordered_groups: list[tuple[str, list[SimplePaperNote]]]) -> str:
    total_count = sum(len(items) for _, items in ordered_groups)
    if not ordered_groups:
        return (
            f"围绕“{project_topic}”暂未形成可供整理的纳入文献。"
            "如需继续推进，建议回看初筛结果中的 uncertain 或扩展检索范围。"
        )

    main_categories = "、".join(name for name, _ in ordered_groups[:4]) if ordered_groups else "若干相关方向"
    if ordered_groups:
        top_name, _top_items = ordered_groups[0]
        top_statement = f"其中以“{top_name}”相关文献数量最多，说明这一方向在当前主题下受到较多关注。"
    else:
        top_statement = ""
    return (
        f"本次纳入文献共 {total_count} 篇，整体上主要分布在{main_categories}等类型。"
        "从研究内容来看，这些文献大多围绕机制阐释、实验验证、干预策略评估或综述性整理展开，"
        f"能够较好地反映当前主题下较受关注的研究切入点与证据积累方向。{top_statement}"
    )


def _build_category_intro(*, category_name: str, count: int, project_topic: str) -> str:
    count_phrase = f"共 {count} 篇" if count > 1 else "目前仅 1 篇"
    return (
        f"该类文献{count_phrase}，主要围绕“{category_name}”这一方向展开。"
        f"就“{project_topic}”而言，这一类型的研究可用于梳理该方向的核心问题、常见研究路径及其参考价值。"
    )


def _trim(text: str, limit: int = 120) -> str:
    cleaned = normalize_text(text) or ""
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _load_existing_notes(path: Path) -> dict[str, SimplePaperNote]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    notes = [SimplePaperNote.model_validate(item) for item in payload]
    return {note.paper_id: note for note in notes}


def _write_notes(notes: list[SimplePaperNote], path: Path) -> None:
    path.write_text(json.dumps([note.model_dump(mode="json") for note in notes], ensure_ascii=False, indent=2), encoding="utf-8")


def _append_log(path: Path, message: str) -> None:
    with path.open("a", encoding="utf-8") as file:
        file.write(message.rstrip() + "\n")


def _emit_progress(
    callback: ProgressCallback | None,
    phase: str,
    label: str,
    current: int | None,
    total: int | None,
    message: str | None = None,
) -> None:
    if callback is not None:
        callback(phase, label, current, total, message)
