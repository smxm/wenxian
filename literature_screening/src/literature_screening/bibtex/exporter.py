from __future__ import annotations

from pathlib import Path
import re

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
    if record.paper_id:
        lines.append(f"ID  - {record.paper_id}")

    for author in record.authors:
        if author:
            lines.append(f"AU  - {author}")
    lines.append(f"TI  - {record.title}")

    volume, number, pages = _extract_bibliographic_details(record)
    if record.year is not None:
        lines.append(f"PY  - {record.year}")
    if record.journal:
        lines.append(f"JO  - {record.journal}")
    if volume:
        lines.append(f"VL  - {volume}")
    if number:
        lines.append(f"IS  - {number}")
    for tag, value in _pages_to_ris_tags(pages):
        lines.append(f"{tag}  - {value}")
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


def _pages_to_ris_tags(pages: str | None) -> list[tuple[str, str]]:
    if not pages:
        return []
    cleaned = str(pages).strip()
    if not cleaned:
        return []
    if "-" not in cleaned:
        return [("SP", cleaned)]
    start, end = cleaned.split("-", 1)
    start = start.strip()
    end = end.strip()
    if start and end:
        return [("SP", start), ("EP", end)]
    if start:
        return [("SP", start)]
    if end:
        return [("EP", end)]
    return []


_FIELD_PATTERNS = {
    "volume": re.compile(r"(?im)^\s*volume\s*=\s*[{\\\"]([^}\\\"]+)[}\\\"],?\s*$"),
    "number": re.compile(r"(?im)^\s*number\s*=\s*[{\\\"]([^}\\\"]+)[}\\\"],?\s*$"),
    "pages": re.compile(r"(?im)^\s*pages\s*=\s*[{\\\"]([^}\\\"]+)[}\\\"],?\s*$"),
}


def _extract_bibliographic_details(record: PaperRecord) -> tuple[str | None, str | None, str | None]:
    values: dict[str, str | None] = {
        "volume": record.volume.strip() if record.volume else None,
        "number": record.number.strip() if record.number else None,
        "pages": record.pages.strip() if record.pages else None,
    }
    raw = record.raw_bibtex or ""
    for key, pattern in _FIELD_PATTERNS.items():
        match = pattern.search(raw)
        if match and not values[key]:
            values[key] = match.group(1).strip()
    return values["volume"], values["number"], values["pages"]
