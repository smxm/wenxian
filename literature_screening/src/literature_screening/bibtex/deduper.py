from __future__ import annotations

from literature_screening.bibtex.normalizer import normalize_title
from literature_screening.core.models import PaperRecord


def deduplicate_records(records: list[PaperRecord]) -> list[PaperRecord]:
    canonical_records: list[PaperRecord] = []
    seen_by_doi: dict[str, PaperRecord] = {}
    seen_by_title: dict[str, PaperRecord] = {}

    for record in records:
        canonical = None
        doi_key = _normalized_doi(record.doi)
        title_key = record.normalized_title or normalize_title(record.title)

        if doi_key and doi_key in seen_by_doi:
            canonical = seen_by_doi[doi_key]
        elif title_key and title_key in seen_by_title:
            canonical = seen_by_title[title_key]

        if canonical is None:
            record.normalized_title = title_key or None
            canonical_records.append(record)
            if doi_key:
                seen_by_doi[doi_key] = record
            if title_key:
                seen_by_title[title_key] = record
            continue

        _merge_record_into(canonical, record)

        if doi_key and doi_key not in seen_by_doi:
            seen_by_doi[doi_key] = canonical
        if title_key and title_key not in seen_by_title:
            seen_by_title[title_key] = canonical

    for index, record in enumerate(canonical_records, start=1):
        record.paper_id = f"paper_{index:06d}"

    return canonical_records


def _merge_record_into(target: PaperRecord, incoming: PaperRecord) -> None:
    target.title = _pick_better_text(target.title, incoming.title)
    target.entry_type = target.entry_type or incoming.entry_type
    target.journal = _pick_better_text(target.journal, incoming.journal)
    target.abstract = _pick_better_text(target.abstract, incoming.abstract)
    target.doi = target.doi or incoming.doi
    target.url = target.url or incoming.url
    target.year = target.year or incoming.year
    target.normalized_title = target.normalized_title or incoming.normalized_title or normalize_title(target.title)
    target.raw_bibtex = _pick_longer_text(target.raw_bibtex, incoming.raw_bibtex)

    if len(incoming.authors) > len(target.authors):
        target.authors = incoming.authors

    target.keywords = _merge_unique(target.keywords, incoming.keywords)
    target.source_files = _merge_unique(target.source_files, incoming.source_files)
    target.source_keys = _merge_unique(target.source_keys, incoming.source_keys)
    target.merged_from = _merge_unique(target.merged_from, [incoming.paper_id, *incoming.merged_from])


def _normalized_doi(value: str | None) -> str | None:
    return value.lower().strip() if value else None


def _merge_unique(existing: list[str], incoming: list[str]) -> list[str]:
    merged = list(existing)
    for item in incoming:
        if item not in merged:
            merged.append(item)
    return merged


def _pick_better_text(existing: str | None, incoming: str | None) -> str | None:
    if existing and incoming:
        return incoming if len(incoming) > len(existing) else existing
    return incoming or existing


def _pick_longer_text(existing: str | None, incoming: str | None) -> str | None:
    if existing and incoming:
        return incoming if len(incoming) > len(existing) else existing
    return incoming or existing
