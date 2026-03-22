from __future__ import annotations

from collections import Counter

from jsonschema import ValidationError, validate

from literature_screening.core.exceptions import SchemaValidationError
from literature_screening.core.schema import BATCH_SCREENING_RESPONSE_SCHEMA


def validate_batch_response(
    payload: dict,
    *,
    expected_batch_id: str | None = None,
    expected_paper_ids: list[str] | None = None,
) -> None:
    try:
        validate(instance=payload, schema=BATCH_SCREENING_RESPONSE_SCHEMA)
    except ValidationError as exc:
        raise SchemaValidationError(f"Batch response schema validation failed: {exc.message}") from exc

    if expected_batch_id is not None and payload["batch_id"] != expected_batch_id:
        raise SchemaValidationError(
            f"Batch response batch_id mismatch: expected '{expected_batch_id}', got '{payload['batch_id']}'."
        )

    if expected_paper_ids is not None:
        _validate_expected_paper_ids(payload, expected_paper_ids)


def _validate_expected_paper_ids(payload: dict, expected_paper_ids: list[str]) -> None:
    returned_paper_ids = [item["paper_id"] for item in payload["results"]]

    if len(returned_paper_ids) != len(expected_paper_ids):
        raise SchemaValidationError(
            f"Batch response result count mismatch: expected {len(expected_paper_ids)}, got {len(returned_paper_ids)}."
        )

    duplicate_ids = [paper_id for paper_id, count in Counter(returned_paper_ids).items() if count > 1]
    if duplicate_ids:
        raise SchemaValidationError(
            f"Batch response contains duplicate paper_id values: {', '.join(sorted(duplicate_ids))}."
        )

    expected_set = set(expected_paper_ids)
    returned_set = set(returned_paper_ids)

    missing_ids = sorted(expected_set - returned_set)
    extra_ids = sorted(returned_set - expected_set)

    if missing_ids or extra_ids:
        message_parts: list[str] = []
        if missing_ids:
            message_parts.append(f"missing paper_id values: {', '.join(missing_ids)}")
        if extra_ids:
            message_parts.append(f"unexpected paper_id values: {', '.join(extra_ids)}")
        raise SchemaValidationError(f"Batch response paper_id mismatch: {'; '.join(message_parts)}.")
