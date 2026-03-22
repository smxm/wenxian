from __future__ import annotations

from jsonschema import ValidationError, validate

from literature_screening.core.exceptions import SchemaValidationError
from literature_screening.formal_report.schema import FORMAL_REPORT_OVERVIEW_SCHEMA
from literature_screening.formal_report.schema import LITERATURE_CARD_SCHEMA


def validate_literature_card(payload: dict) -> None:
    try:
        validate(instance=payload, schema=LITERATURE_CARD_SCHEMA)
    except ValidationError as exc:
        raise SchemaValidationError(f"LiteratureCard schema validation failed: {exc.message}") from exc


def validate_formal_report_overview(
    payload: dict,
    *,
    expected_categories: list[str] | None = None,
    available_paper_ids: list[str] | None = None,
) -> None:
    try:
        validate(instance=payload, schema=FORMAL_REPORT_OVERVIEW_SCHEMA)
    except ValidationError as exc:
        raise SchemaValidationError(f"Formal report overview schema validation failed: {exc.message}") from exc

    if expected_categories is not None:
        returned_categories = [item["category_name"] for item in payload["category_overviews"]]
        missing_categories = sorted(set(expected_categories) - set(returned_categories))
        extra_categories = sorted(set(returned_categories) - set(expected_categories))
        if missing_categories or extra_categories:
            message_parts: list[str] = []
            if missing_categories:
                message_parts.append(f"missing categories: {', '.join(missing_categories)}")
            if extra_categories:
                message_parts.append(f"unexpected categories: {', '.join(extra_categories)}")
            raise SchemaValidationError(f"Formal report category mismatch: {'; '.join(message_parts)}.")

    if available_paper_ids is not None:
        available_set = set(available_paper_ids)
        used_ids: set[str] = set()
        for item in payload["category_overviews"]:
            for paper_id in item["representative_paper_ids"]:
                if paper_id not in available_set:
                    raise SchemaValidationError(
                        f"Formal report overview contains unknown representative paper_id: {paper_id}."
                    )
                used_ids.add(paper_id)

