from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time
import json
from typing import Callable

from literature_screening.bibtex.deduper import deduplicate_records
from literature_screening.bibtex.exporter import export_bibtex
from literature_screening.bibtex.exporter import export_ris
from literature_screening.bibtex.parser import parse_bibtex_files
from literature_screening.core.constants import (
    STATUS_ERROR,
    STATUS_EXCLUDED,
    STATUS_INCLUDED,
    STATUS_UNCERTAIN,
    STATUS_UNPROCESSED,
    STATUS_UNUSED,
    STOP_REASON_ALL_PROCESSED,
    STOP_REASON_MANUAL,
    STOP_REASON_TARGET_REACHED,
)
from literature_screening.core.models import RunConfig, ScreeningDecision
from literature_screening.reporting.report_generator import write_screening_markdown_report
from literature_screening.reporting.writers import write_json
from literature_screening.screening.batcher import build_batch_records
from literature_screening.screening.llm_client import ChatCompletionClient
from literature_screening.screening.prompt_builder import build_screening_prompt
from literature_screening.screening.response_parser import parse_model_json
from literature_screening.screening.validator import validate_batch_response


ProgressCallback = Callable[[str, str, int | None, int | None, str | None], None]


def run_pipeline(
    config: RunConfig,
    dry_run: bool = False,
    progress_callback: ProgressCallback | None = None,
) -> None:
    run_id = f"run_{datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}"
    output_dir = Path(config.project.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "logs").mkdir(exist_ok=True)
    (output_dir / "batches").mkdir(exist_ok=True)

    snapshot_path = output_dir / "config.snapshot.json"
    write_json(config, snapshot_path)

    input_paths = [Path(item) for item in config.input.input_files]
    _emit_progress(progress_callback, "parsing-inputs", "Parsing inputs", 0, None, "Parsing source files")
    merged_records = parse_bibtex_files(input_paths, encoding=config.input.encoding)
    _emit_progress(progress_callback, "deduplicating", "Deduplicating", 0, None, "Removing duplicate records")
    deduped_records = deduplicate_records(merged_records) if config.dedup.enabled else merged_records
    batch_records = build_batch_records(
        deduped_records,
        config.screening.batch_size,
        topic=config.criteria.topic,
        model_provider=config.model.provider,
        model_name=config.model.model_name,
    )
    _emit_progress(
        progress_callback,
        "building-batches",
        "Building batches",
        0,
        len(batch_records),
        f"Prepared {len(batch_records)} screening batches",
    )

    if config.project.save_intermediate_files:
        write_json(merged_records, output_dir / "merged_records.json")
        write_json(deduped_records, output_dir / "deduped_records.json")
        write_json(batch_records, output_dir / "planned_batches.json")
        _write_batch_input_files(output_dir / "batches", batch_records, deduped_records)

    now = datetime.now().astimezone()
    summary = {
        "run_id": run_id,
        "input_files_count": len(input_paths),
        "raw_entries_count": len(merged_records),
        "deduped_entries_count": len(deduped_records),
        "processed_count": 0,
        "included_count": 0,
        "excluded_count": 0,
        "uncertain_count": 0,
        "unused_count": len(deduped_records),
        "batch_count": len(batch_records),
        "api_call_count": 0,
        "stop_reason": STOP_REASON_MANUAL if dry_run else "initialized",
        "started_at": now.isoformat(),
        "finished_at": now.isoformat(),
    }
    write_json(summary, output_dir / "run_summary.json")

    if dry_run:
        _emit_progress(progress_callback, "completed", "Completed", 0, 0, "Dry run completed")
        return

    prompt_template_path = _project_root() / "prompts" / "screening_prompt.md"
    client = ChatCompletionClient(config.model, timeout_seconds=config.screening.request_timeout_seconds)
    decisions: list[ScreeningDecision] = []
    record_map = {record.paper_id: record for record in deduped_records}
    stop_reason = STOP_REASON_ALL_PROCESSED
    processed_batches = 0

    for batch in batch_records:
        _emit_progress(
            progress_callback,
            "screening",
            "Screening batches",
            processed_batches,
            len(batch_records),
            f"Running batch {processed_batches + 1} of {len(batch_records)}",
        )
        batch_output_path = output_dir / "batches" / f"{batch.batch_id}_output.json"
        payload = _load_existing_batch_payload(batch_output_path, batch.batch_id, batch.paper_ids)
        if payload is None:
            batch_papers = [record_map[paper_id] for paper_id in batch.paper_ids if paper_id in record_map]
            prompt = build_screening_prompt(
                template_path=prompt_template_path,
                batch_id=batch.batch_id,
                criteria=config.criteria,
                papers=batch_papers,
            )

            payload = _request_validated_batch_payload(
                client=client,
                prompt=prompt,
                retry_times=config.screening.retry_times,
                batch_id=batch.batch_id,
                expected_paper_ids=batch.paper_ids,
                output_dir=output_dir,
                save_raw_response=config.project.save_raw_response,
            )
            write_json(payload, batch_output_path)
        processed_batches += 1
        _emit_progress(
            progress_callback,
            "screening",
            "Screening batches",
            processed_batches,
            len(batch_records),
            f"Completed batch {processed_batches} of {len(batch_records)}",
        )

        batch_decisions = _payload_to_decisions(payload, batch.batch_id, config)
        decisions.extend(batch_decisions)
        _apply_decisions(record_map, batch_decisions)
        _write_progress_summary(
            output_dir=output_dir,
            run_id=run_id,
            input_paths=input_paths,
            merged_records=merged_records,
            deduped_records=deduped_records,
            record_map=record_map,
            decisions=decisions,
            processed_batches=processed_batches,
            stop_reason="running",
            started_at=now,
        )

        if (
            config.screening.stop_when_target_reached
            and _count_status(record_map.values(), STATUS_INCLUDED) >= config.screening.target_include_count
        ):
            stop_reason = STOP_REASON_TARGET_REACHED
            break

    if stop_reason == STOP_REASON_TARGET_REACHED:
        for record in record_map.values():
            if record.status == STATUS_UNPROCESSED:
                record.status = STATUS_UNUSED

    included_rows = _collect_report_rows(record_map, decisions, STATUS_INCLUDED)
    excluded_rows = _collect_report_rows(record_map, decisions, STATUS_EXCLUDED)
    uncertain_rows = _collect_report_rows(record_map, decisions, STATUS_UNCERTAIN)

    _emit_progress(
        progress_callback,
        "exporting-results",
        "Exporting results",
        processed_batches,
        len(batch_records),
        "Writing reports and RIS/BibTeX exports",
    )
    write_json([decision.model_dump(mode="json") for decision in decisions], output_dir / "screening_decisions.json")
    write_screening_markdown_report(included_rows, "Included Papers", output_dir / "included_report.md")
    write_screening_markdown_report(excluded_rows, "Excluded Papers", output_dir / "excluded_report.md")
    if uncertain_rows:
        write_screening_markdown_report(uncertain_rows, "Uncertain Papers", output_dir / "uncertain_report.md")

    if config.report.export_included_ris:
        export_ris(
            [record for record in record_map.values() if record.status == STATUS_INCLUDED],
            output_dir / "included.ris",
        )
    if config.report.export_excluded_ris:
        export_ris(
            [record for record in record_map.values() if record.status == STATUS_EXCLUDED],
            output_dir / "excluded.ris",
        )
    if config.report.export_unused_ris:
        export_ris(
            [record for record in record_map.values() if record.status == STATUS_UNUSED],
            output_dir / "unused_remaining.ris",
        )
    if config.report.export_included_bib:
        export_bibtex(
            [record for record in record_map.values() if record.status == STATUS_INCLUDED],
            output_dir / "included.bib",
        )
    if config.report.export_excluded_bib:
        export_bibtex(
            [record for record in record_map.values() if record.status == STATUS_EXCLUDED],
            output_dir / "excluded.bib",
        )
    if config.report.export_unused_bib:
        export_bibtex(
            [record for record in record_map.values() if record.status == STATUS_UNUSED],
            output_dir / "unused_remaining.bib",
        )

    finished_at = datetime.now().astimezone()
    final_summary = {
        "run_id": run_id,
        "input_files_count": len(input_paths),
        "raw_entries_count": len(merged_records),
        "deduped_entries_count": len(deduped_records),
        "processed_count": len(decisions),
        "included_count": _count_status(record_map.values(), STATUS_INCLUDED),
        "excluded_count": _count_status(record_map.values(), STATUS_EXCLUDED),
        "uncertain_count": _count_status(record_map.values(), STATUS_UNCERTAIN),
        "unused_count": _count_status(record_map.values(), STATUS_UNUSED),
        "batch_count": processed_batches,
        "api_call_count": processed_batches,
        "stop_reason": stop_reason,
        "started_at": now.isoformat(),
        "finished_at": finished_at.isoformat(),
    }
    write_json(final_summary, output_dir / "run_summary.json")
    _emit_progress(
        progress_callback,
        "completed",
        "Completed",
        processed_batches,
        len(batch_records),
        "Screening task completed",
    )


def _write_batch_input_files(output_dir: Path, batch_records: list, records: list) -> None:
    record_map = {record.paper_id: record for record in records}
    for batch in batch_records:
        payload = {
            "batch_id": batch.batch_id,
            "paper_count": batch.paper_count,
            "paper_ids": batch.paper_ids,
            "papers": [record_map[paper_id] for paper_id in batch.paper_ids if paper_id in record_map],
        }
        write_json(payload, output_dir / f"{batch.batch_id}_input.json")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _request_with_retries(client: ChatCompletionClient, prompt: str, retry_times: int) -> str:
    last_error: Exception | None = None
    for attempt in range(retry_times + 1):
        try:
            return client.chat(prompt)
        except Exception as exc:
            last_error = exc
            if attempt < retry_times:
                delay_seconds = client.extract_retry_after_seconds(exc) or (2 ** attempt)
                time.sleep(delay_seconds)
    assert last_error is not None
    raise last_error


def _request_validated_batch_payload(
    *,
    client: ChatCompletionClient,
    prompt: str,
    retry_times: int,
    batch_id: str,
    expected_paper_ids: list[str],
    output_dir: Path,
    save_raw_response: bool,
) -> dict:
    last_error: Exception | None = None

    for attempt in range(retry_times + 1):
        raw_text = ""
        try:
            raw_text = client.chat(prompt)
            if save_raw_response:
                raw_path = output_dir / "batches" / f"{batch_id}_raw_response_attempt_{attempt + 1:02d}.txt"
                raw_path.write_text(raw_text, encoding="utf-8")

            payload = parse_model_json(raw_text)
            validate_batch_response(
                payload,
                expected_batch_id=batch_id,
                expected_paper_ids=expected_paper_ids,
            )

            if save_raw_response:
                final_raw_path = output_dir / "batches" / f"{batch_id}_raw_response.txt"
                final_raw_path.write_text(raw_text, encoding="utf-8")
            return payload
        except Exception as exc:
            last_error = exc
            if save_raw_response and raw_text:
                failed_raw_path = output_dir / "batches" / f"{batch_id}_raw_response_failed_last.txt"
                failed_raw_path.write_text(raw_text, encoding="utf-8")
            if attempt < retry_times:
                delay_seconds = client.extract_retry_after_seconds(exc) or (2 ** attempt)
                time.sleep(delay_seconds)

    assert last_error is not None
    raise last_error


def _load_existing_batch_payload(
    batch_output_path: Path,
    expected_batch_id: str,
    expected_paper_ids: list[str],
) -> dict | None:
    if not batch_output_path.exists():
        return None

    payload = json.loads(batch_output_path.read_text(encoding="utf-8"))
    validate_batch_response(
        payload,
        expected_batch_id=expected_batch_id,
        expected_paper_ids=expected_paper_ids,
    )
    return payload


def _write_progress_summary(
    *,
    output_dir: Path,
    run_id: str,
    input_paths: list[Path],
    merged_records: list,
    deduped_records: list,
    record_map: dict[str, object],
    decisions: list[ScreeningDecision],
    processed_batches: int,
    stop_reason: str,
    started_at: datetime,
) -> None:
    summary = {
        "run_id": run_id,
        "input_files_count": len(input_paths),
        "raw_entries_count": len(merged_records),
        "deduped_entries_count": len(deduped_records),
        "processed_count": len(decisions),
        "included_count": _count_status(record_map.values(), STATUS_INCLUDED),
        "excluded_count": _count_status(record_map.values(), STATUS_EXCLUDED),
        "uncertain_count": _count_status(record_map.values(), STATUS_UNCERTAIN),
        "unused_count": _count_status(record_map.values(), STATUS_UNUSED) + _count_status(record_map.values(), STATUS_UNPROCESSED),
        "batch_count": processed_batches,
        "api_call_count": processed_batches,
        "stop_reason": stop_reason,
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now().astimezone().isoformat(),
    }
    write_json(summary, output_dir / "run_summary.json")


def _payload_to_decisions(payload: dict, batch_id: str, config: RunConfig) -> list[ScreeningDecision]:
    timestamp = datetime.now().astimezone()
    decisions = []
    for result in payload["results"]:
        decisions.append(
            ScreeningDecision(
                paper_id=result["paper_id"],
                batch_id=batch_id,
                decision=result["decision"],
                reason=result["reason"],
                evidence=result.get("evidence", []),
                confidence=result["confidence"],
                model_provider=config.model.provider,
                model_name=config.model.model_name,
                timestamp=timestamp,
            )
        )
    return decisions


def _apply_decisions(record_map: dict[str, object], decisions: list[ScreeningDecision]) -> None:
    for decision in decisions:
        record = record_map.get(decision.paper_id)
        if record is None:
            continue
        if decision.decision == "include":
            record.status = STATUS_INCLUDED
        elif decision.decision == "exclude":
            record.status = STATUS_EXCLUDED
        elif decision.decision == "uncertain":
            record.status = STATUS_UNCERTAIN
        else:
            record.status = STATUS_ERROR


def _count_status(records, status: str) -> int:
    return sum(1 for record in records if record.status == status)


def _collect_report_rows(
    record_map: dict[str, object],
    decisions: list[ScreeningDecision],
    status: str,
) -> list[tuple]:
    rows = []
    for decision in decisions:
        record = record_map.get(decision.paper_id)
        if record is not None and record.status == status:
            rows.append((record, decision))
    return rows


def _run_with_retries(operation, retry_times: int):
    last_error: Exception | None = None
    for attempt in range(retry_times + 1):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            if attempt < retry_times:
                delay_seconds = ChatCompletionClient.extract_retry_after_seconds(exc) or (2 ** attempt)
                time.sleep(delay_seconds)
    assert last_error is not None
    raise last_error


def _emit_progress(
    callback: ProgressCallback | None,
    phase: str,
    label: str,
    current: int | None,
    total: int | None,
    message: str | None = None,
) -> None:
    if callback is not None:
        callback(phase, label, current, total, message)
