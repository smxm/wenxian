from __future__ import annotations

from pathlib import Path
import re
import unicodedata

from literature_screening.bibtex.normalizer import normalize_title
from literature_screening.core.exceptions import BibtexParseError
from literature_screening.core.models import PaperRecord


def parse_bibtex_files(file_paths: list[Path], encoding: str = "utf-8") -> list[PaperRecord]:
    records: list[PaperRecord] = []
    raw_counter = 0

    for file_path in file_paths:
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        text = _read_bibtex_text(file_path, encoding)
        try:
            entries = _load_entries_for_file(file_path, text)
        except Exception as exc:
            raise BibtexParseError(f"Failed to parse input file: {file_path}") from exc

        for entry in entries:
            raw_counter += 1
            paper_id = _extract_internal_paper_id(entry) or f"raw_{raw_counter:06d}"
            records.append(_entry_to_paper_record(entry, file_path=file_path, paper_id=paper_id))

    return records


_INTERNAL_PAPER_ID_PATTERN = re.compile(r"^(raw|paper)_\d{6}$")


def _extract_internal_paper_id(entry: dict[str, str]) -> str | None:
    candidate = (entry.get("paper_id") or entry.get("ID") or "").strip()
    if not candidate:
        return None
    if _INTERNAL_PAPER_ID_PATTERN.match(candidate):
        return candidate
    return None


def _strip_leading_text(text: str) -> str:
    marker = text.find("@")
    if marker == -1:
        raise BibtexParseError("No BibTeX entry marker '@' found in input text.")
    return text[marker:]


def _load_entries_for_file(file_path: Path, text: str) -> list[dict[str, str]]:
    suffix = file_path.suffix.lower()
    stripped = text.lstrip()

    if suffix == ".enw" or (suffix == ".txt" and stripped.startswith("%0 ")):
        return _parse_endnote_entries(text)
    if suffix == ".ris" or (suffix == ".txt" and stripped.startswith("TY  -")):
        return _parse_ris_entries(text)
    if suffix == ".txt" and _looks_like_pubmed_text(stripped):
        return _parse_pubmed_entries(text)

    payload = _strip_leading_text(text)
    return _load_entries(payload)


def _load_entries(payload: str) -> list[dict[str, str]]:
    try:
        import bibtexparser

        database = bibtexparser.loads(payload)
        return list(database.entries)
    except ImportError:
        return _fallback_parse_entries(payload)


def _fallback_parse_entries(payload: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for block in _split_entry_blocks(payload):
        parsed = _parse_entry_block(block)
        if parsed:
            entries.append(parsed)
    return entries


def _split_entry_blocks(payload: str) -> list[str]:
    blocks: list[str] = []
    index = 0
    while index < len(payload):
        at_pos = payload.find("@", index)
        if at_pos == -1:
            break

        brace_pos = payload.find("{", at_pos)
        if brace_pos == -1:
            break

        depth = 0
        end_pos = None
        for cursor in range(brace_pos, len(payload)):
            char = payload[cursor]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end_pos = cursor
                    break

        if end_pos is None:
            raise BibtexParseError("Unbalanced braces in BibTeX payload.")

        blocks.append(payload[at_pos : end_pos + 1])
        index = end_pos + 1

    return blocks


def _parse_entry_block(block: str) -> dict[str, str]:
    match = re.match(r"@(?P<entry_type>[A-Za-z]+)\s*\{\s*(?P<entry_id>[^,]+)\s*,", block, flags=re.DOTALL)
    if not match:
        raise BibtexParseError("Invalid BibTeX entry header.")

    entry_type = match.group("entry_type").strip()
    entry_id = match.group("entry_id").strip()
    body_start = match.end()
    body = block[body_start:-1].strip()

    fields = {"ENTRYTYPE": entry_type, "ID": entry_id}
    fields.update(_parse_fields(body))
    return fields


def _parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    index = 0

    while index < len(body):
        while index < len(body) and body[index] in " \t\r\n,":
            index += 1
        if index >= len(body):
            break

        key_start = index
        while index < len(body) and body[index] not in "=\r\n":
            index += 1
        key = body[key_start:index].strip().lower()

        while index < len(body) and body[index] != "=":
            index += 1
        if index >= len(body):
            break
        index += 1

        while index < len(body) and body[index] in " \t\r\n":
            index += 1
        if index >= len(body):
            break

        value, index = _parse_value(body, index)
        fields[key] = value

    return fields


def _parse_value(text: str, start: int) -> tuple[str, int]:
    current = text[start]
    if current == "{":
        return _parse_braced_value(text, start)
    if current == '"':
        return _parse_quoted_value(text, start)
    return _parse_plain_value(text, start)


def _parse_braced_value(text: str, start: int) -> tuple[str, int]:
    depth = 0
    index = start
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                value = text[start + 1 : index]
                return value, index + 1
    raise BibtexParseError("Unbalanced braced field in BibTeX entry.")


def _parse_quoted_value(text: str, start: int) -> tuple[str, int]:
    index = start + 1
    escaped = False
    while index < len(text):
        char = text[index]
        if char == '"' and not escaped:
            return text[start + 1 : index], index + 1
        escaped = char == "\\" and not escaped
        index += 1
    raise BibtexParseError("Unterminated quoted field in BibTeX entry.")


def _parse_plain_value(text: str, start: int) -> tuple[str, int]:
    index = start
    while index < len(text) and text[index] not in ",\r\n":
        index += 1
    return text[start:index].strip(), index


def _entry_to_paper_record(entry: dict[str, str], file_path: Path, paper_id: str) -> PaperRecord:
    title = _clean_field(entry.get("title"))
    authors = _parse_authors(entry.get("author", ""))
    keywords = _parse_keywords(entry.get("keywords") or entry.get("author_keywords") or "")

    return PaperRecord(
        paper_id=paper_id,
        entry_type=_clean_field(entry.get("ENTRYTYPE")),
        title=title or f"Untitled record from {file_path.name}",
        authors=authors,
        year=_parse_year(entry.get("year")),
        journal=_clean_field(
            entry.get("journal")
            or entry.get("booktitle")
            or entry.get("school")
            or entry.get("institution")
            or entry.get("publisher")
        ),
        doi=_normalize_doi(entry.get("doi")),
        url=_clean_field(entry.get("url")),
        abstract=_clean_field(
            entry.get("abstract")
            or entry.get("summary")
            or entry.get("note_abstract")
            or entry.get("keywords_abstract")
        ),
        keywords=keywords,
        normalized_title=normalize_title(title) if title else None,
        raw_bibtex=_entry_to_bibtex(entry),
        source_files=[file_path.name],
        source_keys=[_clean_field(entry.get("ID")) or paper_id],
        merged_from=[],
        status="unprocessed",
    )


def _parse_authors(author_field: str) -> list[str]:
    cleaned = _clean_field(author_field)
    if not cleaned:
        return []

    if " and " in cleaned:
        parts = [part.strip() for part in cleaned.split(" and ")]
    elif any(delimiter in cleaned for delimiter in [";", "；", "、"]):
        parts = [part.strip() for part in re.split(r";|；|、", cleaned)]
    elif "，" in cleaned and _contains_cjk(cleaned):
        parts = [part.strip() for part in cleaned.split("，")]
    else:
        parts = [cleaned.strip()]

    return [part for part in parts if part]


def _parse_keywords(keyword_field: str) -> list[str]:
    cleaned = _clean_field(keyword_field)
    if not cleaned:
        return []
    parts = re.split(r";|；|,|，|、", cleaned)
    keywords = []
    for part in parts:
        item = part.strip()
        if item and item not in keywords:
            keywords.append(item)
    return keywords


def _parse_year(value: str | None) -> int | None:
    cleaned = _clean_field(value)
    if not cleaned:
        return None
    match = re.search(r"\d{4}", cleaned)
    return int(match.group()) if match else None


def _normalize_doi(value: str | None) -> str | None:
    cleaned = _clean_field(value)
    if not cleaned:
        return None

    lowered = cleaned.lower().strip()
    prefixes = [
        "https://doi.org/",
        "http://doi.org/",
        "doi:",
    ]
    for prefix in prefixes:
        if lowered.startswith(prefix):
            lowered = lowered[len(prefix) :]
    return lowered or None


def _clean_field(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = unicodedata.normalize("NFKC", value).replace("\n", " ").replace("\r", " ").strip()
    cleaned = cleaned.replace("{", "").replace("}", "")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or None


def _entry_to_bibtex(entry: dict[str, str]) -> str:
    entry_type = _clean_field(entry.get("ENTRYTYPE")) or "article"
    entry_id = _clean_field(entry.get("ID")) or "missing_id"
    field_lines = []

    for key, value in entry.items():
        if key in {"ENTRYTYPE", "ID"}:
            continue
        cleaned = _clean_field(value)
        if cleaned is None:
            continue
        field_lines.append(f"\t{key} = {{{cleaned}}}")

    joined_fields = ",\n".join(field_lines)
    if joined_fields:
        return f"@{entry_type.upper()}{{{entry_id},\n{joined_fields}\n}}"
    return f"@{entry_type.upper()}{{{entry_id}\n}}"


def _parse_endnote_entries(text: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, list[str] | str] = {}
    last_tag: str | None = None
    sequence = 0

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            continue

        if line.startswith("%0 "):
            if current:
                sequence += 1
                records.append(_finalize_endnote_record(current, sequence))
                current = {}
            current["%0"] = line[3:].strip()
            last_tag = "%0"
            continue

        if line.startswith("%") and len(line) >= 3 and line[2] == " ":
            tag = line[:2]
            value = line[3:].strip()
            existing = current.get(tag)
            if existing is None:
                current[tag] = [value] if tag in {"%A", "%K"} else value
            elif isinstance(existing, list):
                existing.append(value)
            else:
                current[tag] = f"{existing}\n{value}" if value else existing
            last_tag = tag
            continue

        if last_tag is not None and last_tag in current:
            existing = current[last_tag]
            if isinstance(existing, list):
                if existing:
                    existing[-1] = f"{existing[-1]} {line.strip()}"
            else:
                current[last_tag] = f"{existing} {line.strip()}"

    if current:
        sequence += 1
        records.append(_finalize_endnote_record(current, sequence))

    return records


def _finalize_endnote_record(raw_record: dict[str, list[str] | str], sequence: int) -> dict[str, str]:
    def get_value(tag: str) -> str | None:
        value = raw_record.get(tag)
        if isinstance(value, list):
            return "; ".join(item for item in value if item)
        return value if isinstance(value, str) else None

    def get_list(tag: str) -> list[str]:
        value = raw_record.get(tag)
        if isinstance(value, list):
            return [item for item in value if item]
        if isinstance(value, str) and value:
            return [value]
        return []

    entry_type_label = (get_value("%0") or "Generic").strip()
    doi_value = get_value("%R")
    title_value = get_value("%T") or f"EndNote record {sequence}"

    entry = {
        "ENTRYTYPE": _map_endnote_type(entry_type_label),
        "ID": doi_value or f"endnote_{sequence:06d}",
        "author": " and ".join(get_list("%A")),
        "title": title_value,
        "journal": get_value("%J"),
        "school": get_value("%I"),
        "publisher": get_value("%I"),
        "year": get_value("%D"),
        "keywords": get_value("%K"),
        "abstract": get_value("%X"),
        "doi": doi_value,
        "url": get_value("%U"),
        "volume": get_value("%V"),
        "number": get_value("%N"),
        "pages": get_value("%P"),
        "issn": get_value("%@"),
        "note": get_value("%W"),
        "language": get_value("%G"),
        "type": get_value("%9"),
    }

    return {key: value for key, value in entry.items() if value not in (None, "")}


def _map_endnote_type(value: str) -> str:
    normalized = value.strip().lower()
    mapping = {
        "journal article": "article",
        "article": "article",
        "thesis": "mastersthesis",
        "master's thesis": "mastersthesis",
        "doctoral dissertation": "phdthesis",
        "conference paper": "inproceedings",
        "book": "book",
        "report": "techreport",
    }
    return mapping.get(normalized, "misc")


def _parse_ris_entries(text: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, list[str]] = {}
    last_tag: str | None = None
    sequence = 0

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            continue

        if re.match(r"^[A-Z0-9]{2}  - ", line):
            tag = line[:2]
            value = line[6:].strip()

            if tag == "TY":
                if current:
                    sequence += 1
                    records.append(_finalize_ris_record(current, sequence))
                    current = {}
                current[tag] = [value]
                last_tag = tag
                continue

            if tag == "ER":
                if current:
                    sequence += 1
                    records.append(_finalize_ris_record(current, sequence))
                    current = {}
                last_tag = None
                continue

            current.setdefault(tag, []).append(value)
            last_tag = tag
            continue

        if last_tag and current.get(last_tag):
            current[last_tag][-1] = f"{current[last_tag][-1]} {line.strip()}".strip()

    if current:
        sequence += 1
        records.append(_finalize_ris_record(current, sequence))

    return records


def _finalize_ris_record(raw_record: dict[str, list[str]], sequence: int) -> dict[str, str]:
    def first(*tags: str) -> str | None:
        for tag in tags:
            values = raw_record.get(tag, [])
            for value in values:
                if value:
                    return value
        return None

    def joined(*tags: str, delimiter: str = "; ") -> str | None:
        collected: list[str] = []
        for tag in tags:
            collected.extend([value for value in raw_record.get(tag, []) if value])
        return delimiter.join(collected) if collected else None

    ris_type = (first("TY") or "GEN").strip()
    doi_value = first("DO")
    start_page = first("SP")
    end_page = first("EP")
    if start_page and end_page:
        pages = f"{start_page}-{end_page}"
    else:
        pages = first("SP", "EP")

    title_value = first("TI", "T1", "CT", "BT") or f"RIS record {sequence}"
    entry_id = first("ID", "AN") or doi_value or f"ris_{sequence:06d}"
    entry = {
        "ENTRYTYPE": _map_ris_type(ris_type),
        "ID": entry_id,
        "author": " and ".join([value for value in raw_record.get("AU", []) + raw_record.get("A1", []) if value]),
        "title": title_value,
        "journal": first("JO", "JF", "JA", "T2", "T3", "PB"),
        "year": first("PY", "Y1", "Y2", "DA"),
        "keywords": joined("KW"),
        "abstract": first("AB", "N2"),
        "doi": doi_value,
        "url": first("UR", "L2", "L1"),
        "volume": first("VL"),
        "number": first("IS", "CP"),
        "pages": pages,
        "issn": first("SN"),
        "publisher": first("PB"),
        "school": first("PB"),
        "note": joined("N1", "M1", "M3"),
        "type": first("M3") or ris_type,
        "source": first("DB"),
    }
    return {key: value for key, value in entry.items() if value not in (None, "")}


def _map_ris_type(value: str) -> str:
    normalized = value.strip().upper()
    mapping = {
        "JOUR": "article",
        "JFULL": "article",
        "MGZN": "article",
        "NEWS": "article",
        "CONF": "inproceedings",
        "CPAPER": "inproceedings",
        "CHAP": "incollection",
        "BOOK": "book",
        "THES": "phdthesis",
        "RPRT": "techreport",
        "ELEC": "misc",
        "GEN": "misc",
    }
    return mapping.get(normalized, "misc")


def _looks_like_pubmed_text(text: str) -> bool:
    return bool(re.match(r"^\d+\.\s", text)) and "PMID:" in text


def _parse_pubmed_entries(text: str) -> list[dict[str, str]]:
    blocks = []
    starts = list(re.finditer(r"(?m)^\d+\.\s", text))
    for index, match in enumerate(starts):
        start = match.start()
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[start:end].strip()
        if block:
            blocks.append(block)

    entries: list[dict[str, str]] = []
    for sequence, block in enumerate(blocks, start=1):
        parsed = _parse_pubmed_block(block, sequence)
        if parsed:
            entries.append(parsed)
    return entries


def _parse_pubmed_block(block: str, sequence: int) -> dict[str, str]:
    lines = [line.rstrip() for line in block.splitlines()]
    index = 0
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        return {}

    citation_lines: list[str] = []
    while index < len(lines) and lines[index].strip():
        citation_lines.append(lines[index].strip())
        index += 1
    normalized_citation = re.sub(r"^\d+\.\s*", "", " ".join(citation_lines).strip())
    index = _skip_blank_lines(lines, index)

    title_lines: list[str] = []
    while index < len(lines) and lines[index].strip():
        title_lines.append(lines[index].strip())
        index += 1
    title = " ".join(title_lines).strip()
    index = _skip_blank_lines(lines, index)

    author_lines: list[str] = []
    while index < len(lines) and lines[index].strip() and lines[index].strip() != "Author information:":
        author_lines.append(lines[index].strip())
        index += 1
    author_field = " ".join(author_lines).strip()
    index = _skip_blank_lines(lines, index)

    if index < len(lines) and lines[index].strip() == "Author information:":
        index += 1
        while index < len(lines) and lines[index].strip():
            index += 1
        index = _skip_blank_lines(lines, index)

    abstract_lines: list[str] = []
    while index < len(lines):
        current = lines[index].strip()
        if not current:
            if abstract_lines:
                break
            index += 1
            continue
        if _is_pubmed_metadata_line(current):
            break
        abstract_lines.append(current)
        index += 1

    abstract = " ".join(abstract_lines).strip()
    doi = _extract_pubmed_doi(normalized_citation, lines)
    pmid = _extract_pubmed_value(lines, "PMID")
    journal = normalized_citation.split(".", 1)[0].strip()

    entry = {
        "ENTRYTYPE": "article",
        "ID": doi or pmid or f"pubmed_{sequence:06d}",
        "author": _normalize_pubmed_authors(author_field),
        "title": title or f"PubMed record {sequence}",
        "journal": journal,
        "year": _extract_pubmed_year(normalized_citation),
        "abstract": abstract,
        "doi": doi,
        "pmid": pmid,
        "note": _extract_pubmed_value(lines, "PMCID"),
    }
    return {key: value for key, value in entry.items() if value not in (None, "")}


def _skip_blank_lines(lines: list[str], index: int) -> int:
    while index < len(lines) and not lines[index].strip():
        index += 1
    return index


def _is_pubmed_metadata_line(line: str) -> bool:
    prefixes = [
        "DOI:",
        "PMCID:",
        "PMID:",
        "Conflict of interest statement:",
        "Copyright",
        "Comment in:",
        "Erratum in:",
        "Erratum for:",
    ]
    return any(line.startswith(prefix) for prefix in prefixes)


def _extract_pubmed_year(citation_line: str) -> str | None:
    match = re.search(r"\b(19|20)\d{2}\b", citation_line)
    return match.group(0) if match else None


def _extract_pubmed_doi(citation_line: str, lines: list[str]) -> str | None:
    citation_match = re.search(r"\bdoi:\s*(10\.\S+)", citation_line, flags=re.IGNORECASE)
    if citation_match:
        return citation_match.group(1).strip().rstrip(".")
    return _extract_pubmed_value(lines, "DOI")


def _extract_pubmed_value(lines: list[str], label: str) -> str | None:
    prefix = f"{label}:"
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return None


def _normalize_pubmed_authors(author_field: str) -> str:
    cleaned = _clean_field(author_field)
    if not cleaned:
        return ""
    parts = [part.strip() for part in re.split(r",\s*(?=[A-Z][A-Za-z'’\-]+(?:\s|$))", cleaned) if part.strip()]
    normalized_parts: list[str] = []
    for part in parts:
        normalized = re.sub(r"\(\d+\)", "", part).strip()
        normalized = normalized.replace("(#)", "")
        normalized = re.sub(r"\s+", " ", normalized).rstrip(".,;")
        if normalized:
            normalized_parts.append(normalized)
    return " and ".join(normalized_parts)


def _read_bibtex_text(file_path: Path, encoding: str) -> str:
    encodings = []
    if encoding and encoding.lower() != "auto":
        encodings.append(encoding)
    encodings.extend(["utf-8-sig", "utf-8", "gb18030", "gbk"])

    tried: list[str] = []
    for candidate in encodings:
        if candidate in tried:
            continue
        tried.append(candidate)
        try:
            return file_path.read_text(encoding=candidate)
        except UnicodeDecodeError:
            continue

    tried_display = ", ".join(tried)
    raise BibtexParseError(f"Failed to decode BibTeX file '{file_path}' with encodings: {tried_display}")


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)
