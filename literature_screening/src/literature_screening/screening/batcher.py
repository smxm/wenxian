from __future__ import annotations

from datetime import datetime

from literature_screening.core.models import PaperRecord
from literature_screening.core.models import BatchRequestRecord


def build_batches(records: list[PaperRecord], batch_size: int) -> list[list[PaperRecord]]:
    return [records[index : index + batch_size] for index in range(0, len(records), batch_size)]


def build_batch_records(
    records: list[PaperRecord],
    batch_size: int,
    *,
    topic: str,
    model_provider: str,
    model_name: str,
) -> list[BatchRequestRecord]:
    batches = build_batches(records, batch_size)
    created_at = datetime.now().astimezone()
    batch_records: list[BatchRequestRecord] = []

    for index, batch in enumerate(batches, start=1):
        batch_records.append(
            BatchRequestRecord(
                batch_id=f"batch_{index:04d}",
                paper_ids=[paper.paper_id for paper in batch],
                paper_count=len(batch),
                criteria_snapshot={"topic": topic},
                model_provider=model_provider,
                model_name=model_name,
                created_at=created_at,
            )
        )

    return batch_records
