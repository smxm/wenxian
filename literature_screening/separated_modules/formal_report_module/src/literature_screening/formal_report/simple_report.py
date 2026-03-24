from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable

from pydantic import BaseModel

from literature_screening.core.models import ModelConfig, PaperRecord, ScreeningDecision
from literature_screening.formal_report.fallback import build_fallback_literature_cards
from literature_screening.formal_report.pipeline import load_included_rows
from literature_screening.formal_report.reference_list import ReferenceStyle, build_reference_block
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


class SimpleReportCategory(BaseModel):
    name: str
    intro: str
    paper_ids: list[str]


class SimpleReportOverview(BaseModel):
    overall_summary: str
    categories: list[SimpleReportCategory]


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
    category_hint_map = {card.paper_id: card.classification.primary_category for card in cards}

    client = ChatCompletionClient(model_config, timeout_seconds=timeout_seconds)
    notes_path = report_output_dir / "paper_notes.json"
    overview_path = report_output_dir / "report_overview.json"
    note_prompt_path = Path(__file__).resolve().parents[3] / "prompts" / "simple_paper_note_prompt.md"
    overview_prompt_path = Path(__file__).resolve().parents[3] / "prompts" / "simple_report_overview_prompt.md"

    notes = _load_existing_notes(notes_path)
    for paper, decision in included_rows:
        if paper.paper_id in notes:
            continue

        completed = len(notes)
        _emit_progress(
            progress_callback,
            "building-paper-notes",
            "Building paper notes",
            completed,
            len(included_rows),
            f"Generating note for {paper.title}",
        )
        category_hint = category_hint_map.get(paper.paper_id, "相关研究")
        try:
            note = _request_note_with_retries(
                client=client,
                prompt_path=note_prompt_path,
                paper=paper,
                decision=decision,
                category_hint=category_hint,
                project_topic=project_topic,
                raw_output_path=report_output_dir / "raw" / f"{paper.paper_id}.txt",
                retry_times=retry_times,
            )
        except Exception as exc:
            _append_log(report_output_dir / "logs" / "paper_note_errors.log", f"{paper.paper_id}: {exc}")
            note = _fallback_note(paper=paper, decision=decision, category_hint=category_hint, project_topic=project_topic)

        notes[note.paper_id] = note
        _write_notes([notes[paper_id] for paper_id in notes], notes_path)

    ordered_notes = [notes[paper.paper_id] for paper, _ in included_rows]
    ordered_papers = [paper for paper, _ in included_rows]

    _emit_progress(
        progress_callback,
        "building-overview",
        "Building overview",
        len(ordered_notes),
        len(ordered_notes),
        "Generating overall summary and category grouping from paper notes",
    )
    try:
        overview = _request_overview_with_retries(
            client=client,
            prompt_path=overview_prompt_path,
            project_topic=project_topic,
            notes=ordered_notes,
            raw_output_path=report_output_dir / "raw" / "report_overview.txt",
            retry_times=retry_times,
        )
    except Exception as exc:
        _append_log(report_output_dir / "logs" / "report_overview_errors.log", str(exc))
        overview = _fallback_overview(project_topic=project_topic, notes=ordered_notes)
    overview_path.write_text(json.dumps(overview.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")

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
        overview=overview,
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
    overview: SimpleReportOverview | None = None,
    records: list[PaperRecord] | None = None,
    reference_style: ReferenceStyle = "gbt7714",
    reference_lines: list[str] | None = None,
) -> str:
    note_map = {note.paper_id: note for note in notes}
    resolved_overview = overview or _fallback_overview(project_topic=project_topic, notes=notes)

    lines = ["# 一、相关文献总体情况", "", resolved_overview.overall_summary.strip(), ""]

    lines.extend(["# 二、类型划分", ""])
    for category in resolved_overview.categories:
        lines.append(f"## {category.name}")
        lines.append("")
        lines.append(category.intro.strip())
        lines.append("")
        for paper_id in category.paper_ids:
            note = note_map.get(paper_id)
            if note is not None:
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
    category_hint: str,
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
                category_hint=category_hint,
                project_topic=project_topic,
            )
            raw_text = client.chat(prompt)
            raw_output_path.write_text(raw_text, encoding="utf-8")
            payload = parse_model_json(raw_text)
            return SimplePaperNote.model_validate(
                {
                    "paper_id": paper.paper_id,
                    "title": normalize_text(paper.title) or paper.title,
                    "category": category_hint,
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


def _request_overview_with_retries(
    *,
    client: ChatCompletionClient,
    prompt_path: Path,
    project_topic: str,
    notes: list[SimplePaperNote],
    raw_output_path: Path,
    retry_times: int,
) -> SimpleReportOverview:
    last_error: Exception | None = None
    for attempt in range(retry_times + 1):
        try:
            prompt = _build_overview_prompt(prompt_path=prompt_path, project_topic=project_topic, notes=notes)
            raw_text = client.chat(prompt)
            raw_output_path.write_text(raw_text, encoding="utf-8")
            payload = parse_model_json(raw_text)
            overview = SimpleReportOverview.model_validate(payload)
            return _normalize_overview(overview=overview, notes=notes, project_topic=project_topic)
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
    category_hint: str,
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
        "category_hint": category_hint,
        "project_topic": project_topic,
    }
    schema = {
        "summary": "string",
        "analysis": "string",
    }
    return template.replace("{{ input_payload }}", json.dumps(payload, ensure_ascii=False, indent=2)).replace(
        "{{ output_schema }}", json.dumps(schema, ensure_ascii=False, indent=2)
    )


def _build_overview_prompt(*, prompt_path: Path, project_topic: str, notes: list[SimplePaperNote]) -> str:
    template = prompt_path.read_text(encoding="utf-8")
    payload = {
        "project_topic": project_topic,
        "notes": [
            {
                "paper_id": note.paper_id,
                "title": note.title,
                "summary": note.summary,
                "analysis": note.analysis,
                "category_hint": note.category,
            }
            for note in notes
        ],
    }
    schema = {
        "overall_summary": "string",
        "categories": [
            {
                "name": "string",
                "intro": "string",
                "paper_ids": ["paper_id_1", "paper_id_2"],
            }
        ],
    }
    return template.replace("{{ input_payload }}", json.dumps(payload, ensure_ascii=False, indent=2)).replace(
        "{{ output_schema }}", json.dumps(schema, ensure_ascii=False, indent=2)
    )


def _fallback_note(
    *,
    paper: PaperRecord,
    decision: ScreeningDecision,
    category_hint: str,
    project_topic: str,
) -> SimplePaperNote:
    title = normalize_text(paper.title) or paper.title
    summary = _fallback_summary(title=title, abstract=normalize_text(paper.abstract), category_hint=category_hint)
    analysis = _fallback_analysis(reason=normalize_text(decision.reason), category_hint=category_hint, project_topic=project_topic)
    return SimplePaperNote(
        paper_id=paper.paper_id,
        title=title,
        category=category_hint,
        summary=summary,
        analysis=analysis,
    )


def _fallback_summary(*, title: str, abstract: str | None, category_hint: str) -> str:
    if abstract:
        first_sentence = abstract.split(". ")[0].split("。")[0].strip()
        if first_sentence:
            return f"该文献围绕“{title}”展开，当前可归入“{category_hint}”相关研究。摘要显示其重点涉及{_trim(first_sentence)}。"
    return f"该文献围绕“{title}”展开，可作为“{category_hint}”方向的参考材料，具体研究设计仍需结合全文进一步确认。"


def _fallback_analysis(*, reason: str | None, category_hint: str, project_topic: str) -> str:
    if reason:
        return f"结合当前主题“{project_topic}”，这篇文献的参考价值主要体现在：{reason}"
    return f"对于“{project_topic}”这一主题，这篇文献可作为“{category_hint}”方向的补充证据，用于梳理该方向的研究切入点和应用价值。"


def _fallback_overview(*, project_topic: str, notes: list[SimplePaperNote]) -> SimpleReportOverview:
    grouped: dict[str, list[SimplePaperNote]] = {}
    for note in notes:
        grouped.setdefault(note.category or "其他相关研究", []).append(note)
    ordered_groups = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    return SimpleReportOverview(
        overall_summary=_build_total_summary(project_topic=project_topic, ordered_groups=ordered_groups),
        categories=[
            SimpleReportCategory(
                name=name,
                intro=_build_category_intro(category_name=name, count=len(items), project_topic=project_topic),
                paper_ids=[item.paper_id for item in items],
            )
            for name, items in ordered_groups
        ],
    )


def _normalize_overview(*, overview: SimpleReportOverview, notes: list[SimplePaperNote], project_topic: str) -> SimpleReportOverview:
    note_ids = [note.paper_id for note in notes]
    valid_ids = set(note_ids)
    assigned: list[str] = []
    categories: list[SimpleReportCategory] = []

    for category in overview.categories:
        cleaned_ids: list[str] = []
        for paper_id in category.paper_ids:
            if paper_id in valid_ids and paper_id not in assigned:
                cleaned_ids.append(paper_id)
                assigned.append(paper_id)
        if cleaned_ids:
            categories.append(
                SimpleReportCategory(
                    name=category.name.strip() or "未命名类型",
                    intro=category.intro.strip() or _build_category_intro(category_name=category.name.strip() or "未命名类型", count=len(cleaned_ids), project_topic=project_topic),
                    paper_ids=cleaned_ids,
                )
            )

    missing = [paper_id for paper_id in note_ids if paper_id not in assigned]
    if missing:
        categories.append(
            SimpleReportCategory(
                name="其他相关文献",
                intro=_build_category_intro(category_name="其他相关文献", count=len(missing), project_topic=project_topic),
                paper_ids=missing,
            )
        )

    overall_summary = overview.overall_summary.strip() or _build_total_summary(
        project_topic=project_topic,
        ordered_groups=[(category.name, [note for note in notes if note.paper_id in category.paper_ids]) for category in categories],
    )
    return SimpleReportOverview(overall_summary=overall_summary, categories=categories)


def _build_total_summary(*, project_topic: str, ordered_groups: list[tuple[str, list[SimplePaperNote]]]) -> str:
    total_count = sum(len(items) for _, items in ordered_groups)
    if not ordered_groups:
        return (
            f"围绕“{project_topic}”暂未形成可供整理的纳入文献。"
            "如需继续推进，建议回看初筛结果中的 uncertain 或扩展检索范围。"
        )

    main_categories = "、".join(name for name, _ in ordered_groups[:4]) if ordered_groups else "若干相关方向"
    top_name, _ = ordered_groups[0]
    return (
        f"本次纳入文献共 {total_count} 篇，整体主要分布在{main_categories}等类型。"
        "从逐篇整理结果看，现有文献主要围绕机制阐释、实验验证、应用评估或综述性整合展开，"
        f"其中“{top_name}”相关文献数量最多，说明这一方向在当前主题下受到较多关注。"
    )


def _build_category_intro(*, category_name: str, count: int, project_topic: str) -> str:
    return (
        f"该类文献共 {count} 篇，主要围绕“{category_name}”这一方向展开。"
        f"就“{project_topic}”而言，这一类型文献可用于梳理该方向的核心问题、常见研究路径及其参考价值。"
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
