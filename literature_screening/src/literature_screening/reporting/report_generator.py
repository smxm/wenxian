from __future__ import annotations

from pathlib import Path

from literature_screening.core.models import PaperRecord, ScreeningDecision


def write_markdown_report(records: list[PaperRecord], title: str, output_path: Path) -> None:
    lines = [f"# {title}", ""]
    for record in records:
        lines.append(f"## {record.title}")
        lines.append("")
        lines.append(f"- paper_id: {record.paper_id}")
        lines.append(f"- status: {record.status}")
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_screening_markdown_report(
    report_rows: list[tuple[PaperRecord, ScreeningDecision]],
    title: str,
    output_path: Path,
) -> None:
    lines = [f"# {title}", ""]

    for paper, decision in report_rows:
        lines.append(f"## {paper.title}")
        lines.append("")
        lines.append(f"- paper_id: {paper.paper_id}")
        lines.append(f"- decision: {decision.decision}")
        lines.append(f"- confidence: {decision.confidence}")
        lines.append(f"- reason: {decision.reason}")
        lines.append(f"- evidence: {', '.join(decision.evidence)}")
        if paper.doi:
            lines.append(f"- doi: {paper.doi}")
        if paper.year is not None:
            lines.append(f"- year: {paper.year}")
        if paper.journal:
            lines.append(f"- journal: {paper.journal}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
