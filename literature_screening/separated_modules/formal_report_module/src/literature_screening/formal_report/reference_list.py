from __future__ import annotations

import json
import re
import subprocess
from typing import Literal
from pathlib import Path

from literature_screening.core.models import PaperRecord
from literature_screening.formal_report.text_utils import normalize_text

ReferenceStyle = Literal["gbt7714", "apa7"]

GB_T_7714_STYLE_URL = (
    "https://raw.githubusercontent.com/zotero-chinese/styles/main/src/"
    "GB-T-7714%E2%80%942015%EF%BC%88%E9%A1%BA%E5%BA%8F%E7%BC%96%E7%A0%81%EF%BC%8C"
    "%E5%8F%8C%E8%AF%AD%EF%BC%8C%E5%A7%93%E5%90%8D%E4%B8%8D%E5%A4%A7%E5%86%99%EF%BC%8C"
    "%E6%97%A0URL%E3%80%81DOI%EF%BC%89/GB-T-7714%E2%80%942015%EF%BC%88%E9%A1%BA%E5%BA%8F"
    "%E7%BC%96%E7%A0%81%EF%BC%8C%E5%8F%8C%E8%AF%AD%EF%BC%8C%E5%A7%93%E5%90%8D%E4%B8%8D%E5%A4%A7"
    "%E5%86%99%EF%BC%8C%E6%97%A0URL%E3%80%81DOI%EF%BC%89.csl"
)
APA7_STYLE_URL = "https://github.com/citation-style-language/styles/blob/master/apa-annotated-bibliography.csl"

_FIELD_PATTERNS = {
    "volume": re.compile(r"(?im)^\s*volume\s*=\s*[{\\\"]([^}\\\"]+)[}\\\"],?\s*$"),
    "number": re.compile(r"(?im)^\s*number\s*=\s*[{\\\"]([^}\\\"]+)[}\\\"],?\s*$"),
    "pages": re.compile(r"(?im)^\s*pages\s*=\s*[{\\\"]([^}\\\"]+)[}\\\"],?\s*$"),
}


def build_reference_list(records: list[PaperRecord], style: ReferenceStyle = "gbt7714") -> list[str]:
    if style == "apa7":
        return [_format_apa7_reference(index, record) for index, record in enumerate(records, start=1)]
    return [_format_gbt7714_reference(index, record) for index, record in enumerate(records, start=1)]


def build_reference_block(
    records: list[PaperRecord],
    *,
    style: ReferenceStyle = "gbt7714",
    working_dir: Path | None = None,
) -> list[str]:
    if style == "apa7" and working_dir is not None:
        rendered = _render_apa7_with_pandoc(records, working_dir)
        if rendered:
            return rendered
    return build_reference_list(records, style=style)


def get_reference_style_note(style: ReferenceStyle) -> str:
    return ""


def _format_gbt7714_reference(index: int, record: PaperRecord) -> str:
    authors = _format_gbt_authors(record.authors)
    title = _clean_title(record.title)
    journal = normalize_text(record.journal) or "Unknown Journal"
    year = str(record.year) if record.year is not None else "n.d."
    volume, number, pages = _extract_bibliographic_details(record)

    source = f"{journal}, {year}"
    if volume:
        source += f", {volume}"
        if number:
            source += f"({number})"
    elif number:
        source += f", ({number})"
    if pages:
        source += f": {pages}"
    source += "."

    return f"[{index}] {authors}. {title}[J]. {source}"


def _format_apa7_reference(index: int, record: PaperRecord) -> str:
    authors = _format_apa_authors(record.authors)
    year = str(record.year) if record.year is not None else "n.d."
    title = _ensure_terminal_punctuation(_clean_title(record.title))
    journal = normalize_text(record.journal) or "Unknown Journal"
    volume, number, pages = _extract_bibliographic_details(record)

    source = journal
    if volume:
        source += f", {volume}"
        if number:
            source += f"({number})"
    elif number:
        source += f", ({number})"
    if pages:
        source += f", {pages}"
    source += "."

    reference = f"[{index}] {authors} ({year}). {title} {source}"
    if record.doi:
        reference += f" https://doi.org/{normalize_text(record.doi)}"
    return reference


def _format_gbt_authors(authors: list[str]) -> str:
    cleaned = [_clean_author_name(author) for author in authors if _clean_author_name(author)]
    if not cleaned:
        return "Unknown Author"
    if len(cleaned) <= 3:
        return ", ".join(cleaned)
    return ", ".join(cleaned[:3]) + ", et al"


def _format_apa_authors(authors: list[str]) -> str:
    cleaned = [_clean_author_name(author) for author in authors if _clean_author_name(author)]
    if not cleaned:
        return "Unknown Author."
    if len(cleaned) == 1:
        return cleaned[0] + "."
    if len(cleaned) <= 7:
        return ", ".join(cleaned[:-1]) + f", & {cleaned[-1]}."
    return ", ".join(cleaned[:6]) + ", ... " + cleaned[-1] + "."


def _clean_author_name(author: str) -> str:
    value = normalize_text(author) or ""
    value = re.sub(r"\s+", " ", value).strip(" ,;.")
    return value


def _clean_title(title: str | None) -> str:
    value = normalize_text(title) or "Untitled"
    return value.strip()


def _ensure_terminal_punctuation(text: str) -> str:
    return text if text.endswith((".", "!", "?", "。", "！", "？")) else text + "."


def _extract_bibliographic_details(record: PaperRecord) -> tuple[str | None, str | None, str | None]:
    values: dict[str, str | None] = {
        "volume": normalize_text(record.volume) if getattr(record, "volume", None) else None,
        "number": normalize_text(record.number) if getattr(record, "number", None) else None,
        "pages": normalize_text(record.pages) if getattr(record, "pages", None) else None,
    }
    raw = record.raw_bibtex or ""
    for key, pattern in _FIELD_PATTERNS.items():
        match = pattern.search(raw)
        if match and not values[key]:
            values[key] = normalize_text(match.group(1))
    return values["volume"], values["number"], values["pages"]


def _render_apa7_with_pandoc(records: list[PaperRecord], working_dir: Path) -> list[str]:
    if not records:
        return []

    pandoc_path = Path(r"C:\Program Files\Pandoc\pandoc.exe")
    csl_path = Path(__file__).resolve().parents[3] / "apa.csl"
    if not pandoc_path.exists() or not csl_path.exists():
        return []

    working_dir.mkdir(parents=True, exist_ok=True)
    bibliography_path = working_dir / "apa_references.json"
    input_path = working_dir / "apa_references_input.md"
    output_path = working_dir / "apa_references_output.html"

    bibliography_path.write_text(
        json.dumps([_paper_record_to_csl_item(record) for record in records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    input_path.write_text(
        "\n".join(
            [
                "---",
                "nocite: |",
                "  @*",
                f'bibliography: "{bibliography_path.name}"',
                f'csl: "{csl_path.as_posix()}"',
                "---",
                "",
                "# References",
                "",
                "::: {#refs}",
                ":::",
                "",
            ]
        ),
        encoding="utf-8",
    )

    subprocess.run(
        [
            str(pandoc_path),
            str(input_path),
            "--citeproc",
            "-t",
            "html",
            "-o",
            str(output_path),
        ],
        cwd=str(working_dir),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    html = output_path.read_text(encoding="utf-8")
    start = html.find("<div id=\"refs\"")
    if start == -1:
        return []
    fragment = html[start:].strip()
    fragment = fragment.replace(
        'class="references csl-bib-body hanging-indent"',
        'class="references csl-bib-body hanging-indent" style="margin-top: 0.5em;"',
    )
    fragment = re.sub(
        r'class="csl-entry" role="listitem"',
        'class="csl-entry" role="listitem" style="margin-left: 2em; text-indent: -2em; margin-bottom: 0.75em;"',
        fragment,
    )
    return fragment.splitlines()


def _paper_record_to_csl_item(record: PaperRecord) -> dict[str, object]:
    volume, number, pages = _extract_bibliographic_details(record)
    item: dict[str, object] = {
        "id": record.paper_id,
        "type": _map_entry_type_to_csl(record.entry_type),
        "title": normalize_text(record.title) or "Untitled",
    }
    if record.journal:
        item["container-title"] = normalize_text(record.journal)
    if record.year is not None:
        item["issued"] = {"date-parts": [[record.year]]}
    if record.doi:
        item["DOI"] = normalize_text(record.doi)
    if volume:
        item["volume"] = volume
    if number:
        item["issue"] = number
    if pages:
        item["page"] = pages

    authors = [_author_to_csl_name(author) for author in record.authors]
    authors = [author for author in authors if author]
    if authors:
        item["author"] = authors
    return item


def _author_to_csl_name(author: str) -> dict[str, str] | None:
    value = _clean_author_name(author)
    if not value:
        return None
    if "," in value:
        left, right = [part.strip() for part in value.split(",", 1)]
        if left and right:
            return {"family": left, "given": _normalize_given_name(right)}
        return {"literal": value}

    tokens = value.split()
    if len(tokens) == 1:
        return {"literal": value}

    last_token = tokens[-1]
    if _looks_like_initials(last_token):
        family = " ".join(tokens[:-1]).strip()
        given = _normalize_given_name(last_token)
        if family and given:
            return {"family": family, "given": given}
        return {"literal": value}

    family = tokens[-1]
    given = " ".join(tokens[:-1]).strip()
    if family and given:
        return {"family": family, "given": given}
    return {"literal": value}


def _looks_like_initials(text: str) -> bool:
    compact = text.replace(".", "").replace("-", "")
    return compact.isalpha() and len(compact) <= 4 and compact.upper() == compact


def _normalize_given_name(text: str) -> str:
    value = normalize_text(text) or ""
    value = value.strip(" ,;.")
    compact = value.replace(" ", "").replace(".", "")
    if compact.isalpha() and len(compact) <= 4 and compact.upper() == compact:
        return " ".join(f"{char}." for char in compact)
    return value


def _map_entry_type_to_csl(entry_type: str | None) -> str:
    normalized = (entry_type or "").strip().lower()
    mapping = {
        "article": "article-journal",
        "inproceedings": "paper-conference",
        "conference": "paper-conference",
        "incollection": "chapter",
        "book": "book",
        "phdthesis": "thesis",
        "mastersthesis": "thesis",
        "techreport": "report",
        "misc": "article",
    }
    return mapping.get(normalized, "article-journal")
