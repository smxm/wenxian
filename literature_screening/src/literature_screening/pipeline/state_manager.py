from __future__ import annotations

from literature_screening.core.models import PaperRecord


def filter_unprocessed(records: list[PaperRecord]) -> list[PaperRecord]:
    return [record for record in records if record.status == "unprocessed"]

