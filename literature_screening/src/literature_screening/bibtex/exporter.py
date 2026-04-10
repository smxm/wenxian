from __future__ import annotations

from pathlib import Path

from literature_screening.core.models import PaperRecord


def export_bibtex(records: list[PaperRecord], output_path: Path) -> None:
    """Export records to a BibTeX file.

    This placeholder writes raw BibTeX blocks separated by blank lines.
    """
    blocks = [record.raw_bibtex for record in records if record.raw_bibtex]
    output_path.write_text("\n\n".join(blocks), encoding="utf-8")


def export_ris(records: list[PaperRecord], output_path: Path) -> None:
    blocks = [_paper_record_to_ris(record) for record in records]
    output_path.write_text("\n\n".join(blocks).strip() + ("\n" if blocks else ""), encoding="utf-8")


def _paper_record_to_ris(record: PaperRecord) -> str:
    lines: list[str] = [f"TY  - {_map_entry_type_to_ris(record.entry_type)}"]

    for author in record.authors:
        if author:
            lines.append(f"AU  - {author}")
    lines.append(f"TI  - {record.title}")

    if record.year is not None:
        lines.append(f"PY  - {record.year}")
    if record.journal:
        lines.append(f"JO  - {record.journal}")
    if record.doi:
        lines.append(f"DO  - {record.doi}")
    if record.url:
        lines.append(f"UR  - {record.url}")
    if record.abstract:
        lines.append(f"AB  - {record.abstract}")
    for keyword in record.keywords:
        if keyword:
            lines.append(f"KW  - {keyword}")

    lines.append("ER  -")
    return "\n".join(lines)


def _map_entry_type_to_ris(entry_type: str | None) -> str:
    normalized = (entry_type or "").strip().lower()
    mapping = {
        "article": "JOUR",
        "inproceedings": "CONF",
        "conference": "CONF",
        "incollection": "CHAP",
        "book": "BOOK",
        "phdthesis": "THES",
        "mastersthesis": "THES",
        "techreport": "RPRT",
        "misc": "GEN",
    }
    return mapping.get(normalized, "GEN")
