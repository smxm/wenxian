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
from literature_screening.core.exceptions import ModelRequestError, ResponseParseError, SchemaValidationError, TaskCancelledError
from literature_screening.core.models import RunConfig, ScreeningDecision
from literature_screening.reporting.report_generator import write_screening_markdown_report
from literature_screening.reporting.writers import write_json
from literature_screening.screening.batcher import build_batch_records
from literature_screening.screening.llm_client import ChatCompletionClient
from literature_screening.screening.prompt_builder import build_screening_prompt
from literature_screening.screening.response_parser import parse_model_json
from literature_screening.screening.validator import validate_batch_response


ProgressCallback = Callable[[str, str, int | None, int | None, str | None], None]
CancelCallback = Callable[[], bool]


def run_pipeline(
    config: RunConfig,
    dry_run: bool = False,
    progress_callback: ProgressCallback | None = None,
    cancel_callback: CancelCallback | None = None,
) -> None:
    run_id = f"run_{datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}"
    output_dir = Path(config.project.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "logs").mkdir(exist_ok=True)
    (output_dir / "batches").mkdir(exist_ok=True)

    snapshot_path = output_dir / "config.snapshot.json"
    write_json(config, snapshot_path)

    input_paths = [Path(item) for item in config.input.input_files]
    _ensure_not_cancelled(cancel_callback)
    _emit_progress(progress_callback, "parsing-inputs", "Parsing inputs", 0, None, "Parsing source files")
    merged_records = parse_bibtex_files(input_paths, encoding=config.input.encoding)
    _ensure_not_cancelled(cancel_callback)
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
        _ensure_not_cancelled(cancel_callback)
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
            payload = _request_batch_payload_with_split_fallback(
                client=client,
                template_path=prompt_template_path,
                criteria=config.criteria,
                min_include_confidence=config.screening.min_include_confidence,
                allow_uncertain=config.screening.allow_uncertain,
                batch_id=batch.batch_id,
                batch_papers=batch_papers,
                retry_times=config.screening.retry_times,
                output_dir=output_dir,
                save_raw_response=config.project.save_raw_response,
                cancel_callback=cancel_callback,
                progress_callback=progress_callback,
                progress_current=processed_batches,
                progress_total=len(batch_records),
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
        progress_summary = _write_progress_summary(
            output_dir=output_dir,
            run_id=run_id,
            input_paths=input_paths,
            merged_records=merged_records,
            deduped_records=deduped_records,
            record_map=record_map,
            decisions=decisions,
            processed_batches=processed_batches,
            api_call_count=client.request_count,
            stop_reason="running",
            started_at=now,
        )
        _emit_progress(
            progress_callback,
            "screening",
            "Screening batches",
            processed_batches,
            len(batch_records),
            (
                f"已筛选 {progress_summary['processed_count']}/{progress_summary['deduped_entries_count']} 篇，"
                f"纳入 {progress_summary['included_count']} 篇，"
                f"剔除 {progress_summary['excluded_count']} 篇，"
                f"不确定 {progress_summary['uncertain_count']} 篇"
            ),
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
        "api_call_count": client.request_count,
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
    cancel_callback: CancelCallback | None = None,
    allow_fast_split: bool = False,
    progress_callback: ProgressCallback | None = None,
    progress_current: int | None = None,
    progress_total: int | None = None,
) -> dict:
    last_error: Exception | None = None
    total_attempts = retry_times + 1

    for attempt in range(total_attempts):
        _ensure_not_cancelled(cancel_callback)
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
            if allow_fast_split and _should_split_without_retry(exc, raw_text, client):
                _emit_progress(
                    progress_callback,
                    "screening",
                    "Screening batches",
                    progress_current,
                    progress_total,
                    f"{batch_id} 返回内容不完整，正在拆分为更小批次",
                )
                raise
            if attempt < retry_times:
                delay_seconds = _retry_delay_seconds(client, exc, attempt)
                _emit_progress(
                    progress_callback,
                    "screening",
                    "Screening batches",
                    progress_current,
                    progress_total,
                    f"{batch_id} 第 {attempt + 1}/{total_attempts} 次请求未通过校验，{delay_seconds} 秒后重试",
                )
                _ensure_not_cancelled(cancel_callback)
                time.sleep(delay_seconds)

    assert last_error is not None
    raise last_error


def _request_batch_payload_with_split_fallback(
    *,
    client: ChatCompletionClient,
    template_path: Path,
    criteria,
    min_include_confidence: float,
    allow_uncertain: bool,
    batch_id: str,
    batch_papers: list,
    retry_times: int,
    output_dir: Path,
    save_raw_response: bool,
    cancel_callback: CancelCallback | None = None,
    progress_callback: ProgressCallback | None = None,
    progress_current: int | None = None,
    progress_total: int | None = None,
) -> dict:
    _ensure_not_cancelled(cancel_callback)
    prompt = build_screening_prompt(
        template_path=template_path,
        batch_id=batch_id,
        criteria=criteria,
        papers=batch_papers,
        min_include_confidence=min_include_confidence,
        allow_uncertain=allow_uncertain,
    )
    expected_paper_ids = [paper.paper_id for paper in batch_papers]

    try:
        return _request_validated_batch_payload(
            client=client,
            prompt=prompt,
            retry_times=retry_times,
            batch_id=batch_id,
            expected_paper_ids=expected_paper_ids,
            output_dir=output_dir,
            save_raw_response=save_raw_response,
            cancel_callback=cancel_callback,
            allow_fast_split=len(batch_papers) > 1,
            progress_callback=progress_callback,
            progress_current=progress_current,
            progress_total=progress_total,
        )
    except (ResponseParseError, SchemaValidationError, ModelRequestError) as exc:
        if isinstance(exc, ModelRequestError) and not _should_split_without_retry(exc, "", client):
            raise
        if len(batch_papers) <= 1:
            raise

    midpoint = len(batch_papers) // 2
    left_papers = batch_papers[:midpoint]
    right_papers = batch_papers[midpoint:]
    _emit_progress(
        progress_callback,
        "screening",
        "Screening batches",
        progress_current,
        progress_total,
        f"{batch_id} 拆分为 {len(left_papers)} + {len(right_papers)} 篇继续筛选",
    )

    left_payload = _request_batch_payload_with_split_fallback(
        client=client,
        template_path=template_path,
        criteria=criteria,
        min_include_confidence=min_include_confidence,
        allow_uncertain=allow_uncertain,
        batch_id=f"{batch_id}_part1",
        batch_papers=left_papers,
        retry_times=retry_times,
        output_dir=output_dir,
        save_raw_response=save_raw_response,
        cancel_callback=cancel_callback,
        progress_callback=progress_callback,
        progress_current=progress_current,
        progress_total=progress_total,
    )
    right_payload = _request_batch_payload_with_split_fallback(
        client=client,
        template_path=template_path,
        criteria=criteria,
        min_include_confidence=min_include_confidence,
        allow_uncertain=allow_uncertain,
        batch_id=f"{batch_id}_part2",
        batch_papers=right_papers,
        retry_times=retry_times,
        output_dir=output_dir,
        save_raw_response=save_raw_response,
        cancel_callback=cancel_callback,
        progress_callback=progress_callback,
        progress_current=progress_current,
        progress_total=progress_total,
    )

    payload = {
        "batch_id": batch_id,
        "results": left_payload["results"] + right_payload["results"],
    }
    validate_batch_response(
        payload,
        expected_batch_id=batch_id,
        expected_paper_ids=expected_paper_ids,
    )
    return payload


def _ensure_not_cancelled(cancel_callback: CancelCallback | None) -> None:
    if cancel_callback and cancel_callback():
        raise TaskCancelledError("Task cancelled by user")


def _retry_delay_seconds(client: ChatCompletionClient, error: Exception, attempt: int) -> int:
    return client.extract_retry_after_seconds(error) or (2 ** attempt)


def _should_split_without_retry(error: Exception, raw_text: str, client: ChatCompletionClient) -> bool:
    finish_reason = getattr(client, "last_finish_reason", None)
    if isinstance(error, (ResponseParseError, SchemaValidationError)) and finish_reason == "length":
        return True
    if isinstance(error, ResponseParseError) and _looks_like_truncated_json(raw_text):
        return True
    if isinstance(error, ModelRequestError):
        text = str(error).lower()
        return "max_tokens" in text or "token limit" in text
    return False


def _looks_like_truncated_json(raw_text: str) -> bool:
    text = raw_text.strip()
    if not text:
        return False

    depth = 0
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if char == '"' and not escaped:
                in_string = False
            escaped = char == "\\" and not escaped
            continue
        if char == '"':
            in_string = True
            escaped = False
            continue
        if char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1

    return in_string or depth > 0 or text.endswith((",", ":", '"'))


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
    api_call_count: int,
    stop_reason: str,
    started_at: datetime,
) -> dict:
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
        "api_call_count": api_call_count,
        "stop_reason": stop_reason,
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now().astimezone().isoformat(),
    }
    write_json(summary, output_dir / "run_summary.json")
    return summary


def _payload_to_decisions(payload: dict, batch_id: str, config: RunConfig) -> list[ScreeningDecision]:
    timestamp = datetime.now().astimezone()
    decisions = []
    min_include_confidence = config.screening.min_include_confidence
    for result in payload["results"]:
        decision_value = result["decision"]
        reason = result["reason"]
        confidence = float(result["confidence"])
        if decision_value == "include" and confidence < min_include_confidence:
            decision_value = "uncertain" if config.screening.allow_uncertain else "exclude"
            reason = _append_include_threshold_reason(reason, min_include_confidence, decision_value)
        decisions.append(
            ScreeningDecision(
                paper_id=result["paper_id"],
                batch_id=batch_id,
                decision=decision_value,
                reason=reason,
                evidence=result.get("evidence", []),
                confidence=confidence,
                model_provider=config.model.provider,
                model_name=config.model.model_name,
                timestamp=timestamp,
            )
        )
    return decisions


def _append_include_threshold_reason(reason: str, min_include_confidence: float, next_decision: str) -> str:
    threshold_percent = round(min_include_confidence * 100)
    next_label = "不确定" if next_decision == "uncertain" else "剔除"
    suffix = f"相关度低于本轮最低纳入阈值 {threshold_percent}%，已转为{next_label}。"
    return f"{reason.rstrip('。.')}。{suffix}" if reason else suffix


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
