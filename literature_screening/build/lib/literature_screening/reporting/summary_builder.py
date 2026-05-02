from __future__ import annotations

from datetime import datetime

from literature_screening.core.models import RunSummary


def build_empty_summary(run_id: str, stop_reason: str) -> RunSummary:
    now = datetime.now().astimezone()
    return RunSummary(
        run_id=run_id,
        stop_reason=stop_reason,
        started_at=now,
        finished_at=now,
    )

