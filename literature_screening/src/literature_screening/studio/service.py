from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import yaml

from literature_screening.storage_paths import rewrite_storage_payload


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAIN_SRC = PROJECT_ROOT / "src"
DETACHED_MODULE_ROOT = PROJECT_ROOT / "separated_modules" / "formal_report_module"
DETACHED_SRC = DETACHED_MODULE_ROOT / "src"
DEFAULT_RUNS_ROOT = PROJECT_ROOT / "data" / "studio_runs"
SUPPORTED_INPUT_SUFFIXES = {".bib", ".enw", ".ris", ".txt"}
ProgressCallback = Callable[[str, str, int | None, int | None, str | None], None]


def bootstrap_project_paths() -> None:
    if str(MAIN_SRC) not in sys.path:
        sys.path.insert(0, str(MAIN_SRC))

    import literature_screening

    detached_pkg_root = DETACHED_SRC / "literature_screening"
    if str(detached_pkg_root) not in list(literature_screening.__path__):
        literature_screening.__path__.append(str(detached_pkg_root))

    from literature_screening.core.env import load_dotenv_file

    load_dotenv_file(PROJECT_ROOT / ".env")


@dataclass(slots=True)
class CriteriaDraft:
    topic: str
    inclusion: list[str]
    exclusion: list[str]
    source_path: str | None = None


@dataclass(slots=True)
class ModelDraft:
    provider: str
    model_name: str
    api_base_url: str
    api_key_env: str
    api_key: str | None = None
    temperature: float = 0.0
    max_tokens: int = 4096
    min_request_interval_seconds: float = 2.0


@dataclass(slots=True)
class StrategyJobRequest:
    project_name: str
    project_topic: str
    research_need: str
    selected_databases: list[str]
    model: ModelDraft
    runs_root: Path = DEFAULT_RUNS_ROOT
    run_root_override: Path | None = None
    timeout_seconds: int = 180


@dataclass(slots=True)
class StrategyJobResult:
    run_root: Path
    output_dir: Path
    summary: dict[str, Any]
    markdown: str
    artifacts: dict[str, Path]


@dataclass(slots=True)
class ScreeningJobRequest:
    project_name: str
    input_paths: list[Path]
    criteria: CriteriaDraft
    model: ModelDraft
    runs_root: Path = DEFAULT_RUNS_ROOT
    storage_root: Path | None = None
    run_root_override: Path | None = None
    batch_size: int = 10
    target_include_count: int = 9999
    stop_when_target_reached: bool = False
    min_include_confidence: float = 0.8
    allow_uncertain: bool = True
    retry_times: int = 8
    request_timeout_seconds: int = 240
    encoding: str = "auto"
    strict_doi_match: bool = True
    normalized_title_exact_match: bool = True
    fuzzy_title_match: bool = False
    export_included_ris: bool = True
    export_excluded_ris: bool = False
    export_unused_ris: bool = True
    export_included_bib: bool = False
    export_excluded_bib: bool = False
    export_unused_bib: bool = False


@dataclass(slots=True)
class ScreeningJobResult:
    run_slug: str
    run_root: Path
    config_path: Path
    output_dir: Path
    summary: dict[str, Any]
    records: list[dict[str, Any]]
    reports: dict[str, Path]
    project_name: str = ""
    criteria_topic: str = ""
    copied_input_paths: list[Path] = field(default_factory=list)


@dataclass(slots=True)
class ReportJobRequest:
    screening_output_dir: Path
    project_topic: str
    model: ModelDraft
    report_name: str = "simple_report"
    runs_root: Path = DEFAULT_RUNS_ROOT
    report_output_dir_override: Path | None = None
    shared_notes_cache_dir: Path | None = None
    timeout_seconds: int = 240
    retry_times: int = 6
    reference_style: str = "gbt7714"


@dataclass(slots=True)
class ReportJobResult:
    run_root: Path
    report_output_dir: Path
    report_path: Path
    notes_path: Path
    markdown: str


def parse_criteria_markdown_text(text: str, source_path: str | None = None) -> CriteriaDraft:
    normalized = text.replace("\r\n", "\n")
    topic = _extract_topic(normalized) or "Untitled literature screening topic"
    inclusion = _extract_criteria_items(normalized, ["纳入标准", "Inclusion", "Inclusion Criteria"])
    exclusion = _extract_criteria_items(normalized, ["排除标准", "Exclusion", "Exclusion Criteria"])
    return CriteriaDraft(
        topic=topic,
        inclusion=inclusion or ["Please fill in inclusion criteria."],
        exclusion=exclusion or ["Please fill in exclusion criteria."],
        source_path=source_path,
    )


def scan_supported_input_files(folder: Path) -> list[Path]:
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Input folder not found: {folder}")

    files = [path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_SUFFIXES]
    return sorted(files, key=lambda item: item.name.lower())


def run_screening_job(
    request: ScreeningJobRequest,
    progress_callback: ProgressCallback | None = None,
    cancel_callback: Callable[[], bool] | None = None,
) -> ScreeningJobResult:
    bootstrap_project_paths()

    from literature_screening.core.models import CriteriaConfig
    from literature_screening.core.models import DedupConfig
    from literature_screening.core.models import InputConfig
    from literature_screening.core.models import ModelConfig
    from literature_screening.core.models import ProjectConfig
    from literature_screening.core.models import ReportConfig
    from literature_screening.core.models import RunConfig
    from literature_screening.core.models import ScreeningConfig
    from literature_screening.pipeline.run_pipeline import run_pipeline

    if request.run_root_override is not None:
        run_root = request.run_root_override
        run_slug = run_root.name
    else:
        run_slug = _build_run_slug(request.project_name)
        run_root = request.runs_root / run_slug
    input_dir = run_root / "inputs"
    criteria_dir = run_root / "criteria"
    output_dir = run_root / "screening_output"

    input_dir.mkdir(parents=True, exist_ok=True)
    criteria_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    _emit_progress(progress_callback, "preparing-inputs", "Preparing inputs", 0, None, "Copying uploaded files")

    copied_input_paths = _copy_input_files(request.input_paths, input_dir)
    criteria_path = criteria_dir / "criteria.md"
    criteria_path.write_text(_render_criteria_markdown(request.criteria), encoding="utf-8")
    _emit_progress(
        progress_callback,
        "building-config",
        "Building configuration",
        0,
        None,
        "Creating screening config snapshot",
    )

    config_payload = {
        "project": {
            "name": request.project_name,
            "output_dir": str(output_dir),
            "save_raw_response": True,
            "save_intermediate_files": True,
        },
        "input": {
            "input_files": [str(path) for path in copied_input_paths],
            "encoding": request.encoding,
        },
        "dedup": {
            "enabled": True,
            "strict_doi_match": request.strict_doi_match,
            "normalized_title_exact_match": request.normalized_title_exact_match,
            "fuzzy_title_match": request.fuzzy_title_match,
        },
        "screening": {
            "batch_size": request.batch_size,
            "target_include_count": request.target_include_count,
            "stop_when_target_reached": request.stop_when_target_reached,
            "min_include_confidence": request.min_include_confidence,
            "allow_uncertain": request.allow_uncertain,
            "retry_times": request.retry_times,
            "request_timeout_seconds": request.request_timeout_seconds,
        },
        "criteria": {
            "topic": request.criteria.topic,
            "inclusion": request.criteria.inclusion,
            "exclusion": request.criteria.exclusion,
        },
        "model": {
            "provider": request.model.provider,
            "model_name": request.model.model_name,
            "api_base_url": request.model.api_base_url,
            "api_key_env": request.model.api_key_env,
            "temperature": request.model.temperature,
            "max_tokens": request.model.max_tokens,
            "min_request_interval_seconds": request.model.min_request_interval_seconds,
        },
        "report": {
            "export_included_ris": request.export_included_ris,
            "export_excluded_ris": request.export_excluded_ris,
            "export_unused_ris": request.export_unused_ris,
            "export_included_bib": request.export_included_bib,
            "export_excluded_bib": request.export_excluded_bib,
            "export_unused_bib": request.export_unused_bib,
            "included_report_format": "md",
            "excluded_report_format": "md",
            "summary_format": "json",
        },
    }

    snapshot_payload = (
        rewrite_storage_payload(config_payload, storage_root=request.storage_root, mode="dehydrate")
        if request.storage_root is not None
        else config_payload
    )
    config_path = run_root / "generated_screening_config.yaml"
    config_path.write_text(yaml.safe_dump(snapshot_payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    run_config = RunConfig(
        project=ProjectConfig(**config_payload["project"]),
        input=InputConfig(**config_payload["input"]),
        dedup=DedupConfig(**config_payload["dedup"]),
        screening=ScreeningConfig(**config_payload["screening"]),
        criteria=CriteriaConfig(**config_payload["criteria"]),
        model=ModelConfig(**config_payload["model"], api_key=request.model.api_key),
        report=ReportConfig(**config_payload["report"]),
    )
    run_pipeline(run_config, dry_run=False, progress_callback=progress_callback, cancel_callback=cancel_callback)

    summary = _load_json(output_dir / "run_summary.json")
    records = load_screening_records(output_dir)
    reports = {
        "included_report": output_dir / "included_report.md",
        "excluded_report": output_dir / "excluded_report.md",
        "uncertain_report": output_dir / "uncertain_report.md",
        "included_ris": output_dir / "included.ris",
        "excluded_ris": output_dir / "excluded.ris",
        "unused_ris": output_dir / "unused_remaining.ris",
        "included_bib": output_dir / "included.bib",
        "excluded_bib": output_dir / "excluded.bib",
        "unused_bib": output_dir / "unused_remaining.bib",
    }
    return ScreeningJobResult(
        run_slug=run_slug,
        run_root=run_root,
        config_path=config_path,
        output_dir=output_dir,
        summary=summary,
        records=records,
        reports=reports,
        project_name=request.project_name,
        criteria_topic=request.criteria.topic,
        copied_input_paths=copied_input_paths,
    )


def recover_screening_job_result(
    run_root: Path,
    *,
    project_name: str = "",
    criteria_topic: str = "",
    stop_reason: str = "manual_stop",
) -> ScreeningJobResult | None:
    bootstrap_project_paths()

    from literature_screening.bibtex.exporter import export_bibtex
    from literature_screening.bibtex.exporter import export_ris
    from literature_screening.core.constants import STATUS_EXCLUDED
    from literature_screening.core.constants import STATUS_INCLUDED
    from literature_screening.core.constants import STATUS_UNCERTAIN
    from literature_screening.core.constants import STATUS_UNPROCESSED
    from literature_screening.core.constants import STATUS_UNUSED
    from literature_screening.core.models import PaperRecord
    from literature_screening.core.models import ScreeningDecision
    from literature_screening.reporting.report_generator import write_screening_markdown_report
    from literature_screening.reporting.writers import write_json

    output_dir = run_root / "screening_output"
    batch_dir = output_dir / "batches"
    records_path = output_dir / "deduped_records.json"
    snapshot_path = output_dir / "config.snapshot.json"
    config_path = run_root / "generated_screening_config.yaml"
    summary_path = output_dir / "run_summary.json"

    if not batch_dir.exists() or not records_path.exists() or not snapshot_path.exists():
        return None

    batch_output_paths = sorted(batch_dir.glob("batch_*_output.json"))
    if not batch_output_paths:
        return None

    records_payload = _load_json(records_path)
    config_payload = _load_json(snapshot_path)
    summary_payload = _load_json(summary_path) if summary_path.exists() else {}

    record_map = {
        item["paper_id"]: PaperRecord.model_validate(item)
        for item in records_payload
        if isinstance(item, dict) and item.get("paper_id")
    }
    model_payload = config_payload.get("model", {}) if isinstance(config_payload, dict) else {}
    report_payload = config_payload.get("report", {}) if isinstance(config_payload, dict) else {}

    decisions: list[ScreeningDecision] = []
    for batch_output_path in batch_output_paths:
        payload = _load_json(batch_output_path)
        batch_id = str(payload.get("batch_id") or batch_output_path.stem.removesuffix("_output"))
        timestamp = datetime.fromtimestamp(batch_output_path.stat().st_mtime).astimezone()
        for result in payload.get("results", []):
            paper_id = str(result.get("paper_id") or "").strip()
            if not paper_id or paper_id not in record_map:
                continue
            decision = ScreeningDecision(
                paper_id=paper_id,
                batch_id=batch_id,
                decision=result["decision"],
                reason=str(result.get("reason") or ""),
                evidence=list(result.get("evidence") or []),
                confidence=float(result["confidence"]),
                model_provider=str(model_payload.get("provider") or "system"),
                model_name=str(model_payload.get("model_name") or "partial-recovery"),
                timestamp=timestamp,
            )
            decisions.append(decision)
            if decision.decision == "include":
                record_map[paper_id].status = STATUS_INCLUDED
            elif decision.decision == "exclude":
                record_map[paper_id].status = STATUS_EXCLUDED
            elif decision.decision == "uncertain":
                record_map[paper_id].status = STATUS_UNCERTAIN

    if not decisions:
        return None

    for record in record_map.values():
        if record.status == STATUS_UNPROCESSED:
            record.status = STATUS_UNUSED

    included_rows = [(record_map[decision.paper_id], decision) for decision in decisions if record_map[decision.paper_id].status == STATUS_INCLUDED]
    excluded_rows = [(record_map[decision.paper_id], decision) for decision in decisions if record_map[decision.paper_id].status == STATUS_EXCLUDED]
    uncertain_rows = [(record_map[decision.paper_id], decision) for decision in decisions if record_map[decision.paper_id].status == STATUS_UNCERTAIN]

    decisions_path = output_dir / "screening_decisions.json"
    included_report_path = output_dir / "included_report.md"
    excluded_report_path = output_dir / "excluded_report.md"
    uncertain_report_path = output_dir / "uncertain_report.md"
    included_ris_path = output_dir / "included.ris"
    excluded_ris_path = output_dir / "excluded.ris"
    unused_ris_path = output_dir / "unused_remaining.ris"
    included_bib_path = output_dir / "included.bib"
    excluded_bib_path = output_dir / "excluded.bib"
    unused_bib_path = output_dir / "unused_remaining.bib"

    write_json([decision.model_dump(mode="json") for decision in decisions], decisions_path)
    write_screening_markdown_report(included_rows, "Included Papers", included_report_path)
    write_screening_markdown_report(excluded_rows, "Excluded Papers", excluded_report_path)
    if uncertain_rows:
        write_screening_markdown_report(uncertain_rows, "Uncertain Papers", uncertain_report_path)
    elif uncertain_report_path.exists():
        uncertain_report_path.unlink()

    included_records = [record for record in record_map.values() if record.status == STATUS_INCLUDED]
    excluded_records = [record for record in record_map.values() if record.status == STATUS_EXCLUDED]
    unused_records = [record for record in record_map.values() if record.status == STATUS_UNUSED]

    if report_payload.get("export_included_ris", True):
        export_ris(included_records, included_ris_path)
    elif included_ris_path.exists():
        included_ris_path.unlink()

    if report_payload.get("export_excluded_ris", False):
        export_ris(excluded_records, excluded_ris_path)
    elif excluded_ris_path.exists():
        excluded_ris_path.unlink()

    if report_payload.get("export_unused_ris", True):
        export_ris(unused_records, unused_ris_path)
    elif unused_ris_path.exists():
        unused_ris_path.unlink()

    if report_payload.get("export_included_bib", False):
        export_bibtex(included_records, included_bib_path)
    elif included_bib_path.exists():
        included_bib_path.unlink()

    if report_payload.get("export_excluded_bib", False):
        export_bibtex(excluded_records, excluded_bib_path)
    elif excluded_bib_path.exists():
        excluded_bib_path.unlink()

    if report_payload.get("export_unused_bib", False):
        export_bibtex(unused_records, unused_bib_path)
    elif unused_bib_path.exists():
        unused_bib_path.unlink()

    started_at = str(summary_payload.get("started_at") or datetime.now().astimezone().isoformat())
    final_summary = {
        "run_id": summary_payload.get("run_id") or f"run_{datetime.now().astimezone().strftime('%Y%m%d_%H%M%S')}",
        "input_files_count": int(summary_payload.get("input_files_count") or 0),
        "raw_entries_count": int(summary_payload.get("raw_entries_count") or len(records_payload)),
        "deduped_entries_count": int(summary_payload.get("deduped_entries_count") or len(record_map)),
        "processed_count": len(decisions),
        "included_count": len(included_records),
        "excluded_count": len(excluded_records),
        "uncertain_count": len(uncertain_rows),
        "unused_count": len(unused_records),
        "batch_count": len(batch_output_paths),
        "api_call_count": len(batch_output_paths),
        "stop_reason": stop_reason,
        "started_at": started_at,
        "finished_at": datetime.now().astimezone().isoformat(),
    }
    write_json(final_summary, summary_path)

    reports = {
        "included_report": included_report_path,
        "excluded_report": excluded_report_path,
        "uncertain_report": uncertain_report_path,
        "included_ris": included_ris_path,
        "excluded_ris": excluded_ris_path,
        "unused_ris": unused_ris_path,
        "included_bib": included_bib_path,
        "excluded_bib": excluded_bib_path,
        "unused_bib": unused_bib_path,
    }
    return ScreeningJobResult(
        run_slug=run_root.name,
        run_root=run_root,
        config_path=config_path,
        output_dir=output_dir,
        summary=final_summary,
        records=load_screening_records(output_dir),
        reports=reports,
        project_name=project_name,
        criteria_topic=criteria_topic,
        copied_input_paths=sorted((run_root / "inputs").glob("*")),
    )


def generate_strategy_job(
    request: StrategyJobRequest,
    progress_callback: ProgressCallback | None = None,
) -> StrategyJobResult:
    bootstrap_project_paths()

    from literature_screening.core.models import ModelConfig
    from literature_screening.strategy.generator import generate_search_strategy

    run_root = request.run_root_override or (request.runs_root / _build_run_slug(request.project_name))
    output_dir = run_root / "strategy_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    _emit_progress(
        progress_callback,
        "building-strategy",
        "Building strategy",
        0,
        None,
        "Generating search syntax and reusable screening criteria",
    )

    plan = generate_search_strategy(
        research_need=request.research_need,
        selected_databases=request.selected_databases,
        model_config=ModelConfig(
            provider=request.model.provider,
            model_name=request.model.model_name,
            api_base_url=request.model.api_base_url,
            api_key_env=request.model.api_key_env,
            api_key=request.model.api_key,
            temperature=request.model.temperature,
            max_tokens=request.model.max_tokens,
            min_request_interval_seconds=request.model.min_request_interval_seconds,
        ),
        timeout_seconds=request.timeout_seconds,
        output_dir=output_dir,
    )

    strategy_md = output_dir / "strategy_plan.md"
    strategy_json = output_dir / "strategy_plan.json"
    raw_response = output_dir / "strategy_raw_response.txt"
    return StrategyJobResult(
        run_root=run_root,
        output_dir=output_dir,
        summary={
            "topic": plan.topic,
            "screening_topic": plan.screening_topic,
            "selected_databases": request.selected_databases,
            "database_count": len(plan.search_blocks),
            "inclusion_count": len(plan.inclusion),
            "exclusion_count": len(plan.exclusion),
        },
        markdown=strategy_md.read_text(encoding="utf-8") if strategy_md.exists() else "",
        artifacts={
            "strategy_plan": strategy_md,
            "strategy_plan_json": strategy_json,
            "strategy_raw_response": raw_response,
        },
    )


def generate_simple_report_job(
    request: ReportJobRequest,
    progress_callback: ProgressCallback | None = None,
) -> ReportJobResult:
    bootstrap_project_paths()

    from literature_screening.core.models import ModelConfig
    from literature_screening.formal_report.simple_report import DEFAULT_SIMPLE_REPORT_FILENAME
    from literature_screening.formal_report.simple_report import generate_simple_report

    report_output_dir = request.report_output_dir_override or (request.screening_output_dir.parent / f"{request.report_name}_output")
    report_output_dir.mkdir(parents=True, exist_ok=True)
    _emit_progress(
        progress_callback,
        "loading-screening-results",
        "Loading screening results",
        0,
        None,
        "Reading included papers from screening output",
    )

    model_config = ModelConfig(
        provider=request.model.provider,
        model_name=request.model.model_name,
        api_base_url=request.model.api_base_url,
        api_key_env=request.model.api_key_env,
        api_key=request.model.api_key,
        temperature=request.model.temperature,
        max_tokens=request.model.max_tokens,
        min_request_interval_seconds=request.model.min_request_interval_seconds,
    )
    generate_simple_report(
        screening_output_dir=request.screening_output_dir,
        report_output_dir=report_output_dir,
        shared_notes_cache_dir=request.shared_notes_cache_dir,
        project_topic=request.project_topic,
        model_config=model_config,
        timeout_seconds=request.timeout_seconds,
        retry_times=request.retry_times,
        reference_style=request.reference_style,
        progress_callback=progress_callback,
    )
    report_path = report_output_dir / DEFAULT_SIMPLE_REPORT_FILENAME
    notes_path = report_output_dir / "paper_notes.json"
    markdown = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    return ReportJobResult(
        run_root=report_output_dir.parent,
        report_output_dir=report_output_dir,
        report_path=report_path,
        notes_path=notes_path,
        markdown=markdown,
    )


def load_screening_records(output_dir: Path) -> list[dict[str, Any]]:
    records_path = output_dir / "deduped_records.json"
    decisions_path = output_dir / "screening_decisions.json"
    if not records_path.exists() or not decisions_path.exists():
        return []

    records = _load_json(records_path)
    decisions = _load_json(decisions_path)
    record_map = {item["paper_id"]: item for item in records}

    rows: list[dict[str, Any]] = []
    for decision in decisions:
        paper = record_map.get(decision["paper_id"], {})
        rows.append(
            {
                "paper_id": decision["paper_id"],
                "title": paper.get("title", ""),
                "decision": decision.get("decision", ""),
                "confidence": decision.get("confidence", ""),
                "reason": decision.get("reason", ""),
                "year": paper.get("year"),
                "journal": paper.get("journal", ""),
                "doi": paper.get("doi", ""),
                "abstract": paper.get("abstract", ""),
            }
        )
    return rows


def save_uploaded_file_bytes(files: list[tuple[str, bytes]], target_dir: Path) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for name, content in files:
        path = target_dir / Path(name).name
        path.write_bytes(content)
        saved.append(path)
    return saved


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _copy_input_files(input_paths: list[Path], target_dir: Path) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    copied_paths: list[Path] = []
    for path in input_paths:
        destination = target_dir / path.name
        shutil.copy2(path, destination)
        copied_paths.append(destination)
    return copied_paths


def _build_run_slug(project_name: str) -> str:
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", project_name.strip()).strip("-").lower()
    slug = slug or "literature-run"
    return f"{timestamp}_{slug}"


def _extract_topic(text: str) -> str:
    for line in text.split("\n"):
        stripped = line.strip().lstrip("#").strip()
        if not stripped:
            continue
        if any(label in stripped.lower() for label in ["inclusion", "exclusion"]):
            continue
        return stripped
    return ""


def _extract_criteria_items(text: str, labels: list[str]) -> list[str]:
    lines = text.split("\n")
    items: list[str] = []
    active = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        is_heading = stripped.startswith("#")
        heading_text = stripped.lstrip("#").strip()
        if is_heading:
            active = any(label.lower() in heading_text.lower() for label in labels)
            continue
        if any(other.lower() in heading_text.lower() for other in ["inclusion", "exclusion"]):
            active = False
        if active and stripped.startswith(("-", "*")):
            item = stripped.lstrip("-*").strip()
            if item:
                items.append(item)
    if items:
        return items

    inline_items: list[str] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        for label in labels:
            if stripped.lower().startswith(label.lower()):
                tail = stripped[len(label):].lstrip(":：").strip()
                inline_items.extend(part.strip() for part in re.split(r"[;；]", tail) if part.strip())
    return inline_items


def _render_criteria_markdown(criteria: CriteriaDraft) -> str:
    lines = ["# Topic", "", criteria.topic, "", "## Inclusion", ""]
    lines.extend([f"- {item}" for item in criteria.inclusion])
    lines.extend(["", "## Exclusion", ""])
    lines.extend([f"- {item}" for item in criteria.exclusion])
    return "\n".join(lines).strip() + "\n"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def prepare_virtual_screening_output_from_dataset_paths(dataset_paths: list[Path], output_dir: Path) -> Path:
    bootstrap_project_paths()

    from literature_screening.bibtex.deduper import deduplicate_records
    from literature_screening.bibtex.parser import parse_bibtex_files
    from literature_screening.core.models import ScreeningDecision

    output_dir.mkdir(parents=True, exist_ok=True)
    records = parse_bibtex_files(dataset_paths, encoding="auto")
    deduped_records = deduplicate_records(records)
    decisions = [
        ScreeningDecision(
            paper_id=record.paper_id,
            batch_id="virtual_dataset",
            decision="include",
            reason="Selected from reusable project dataset.",
            evidence=[],
            confidence=1.0,
            model_provider="system",
            model_name="dataset-loader",
            timestamp=datetime.now().astimezone(),
        )
        for record in deduped_records
    ]
    (output_dir / "deduped_records.json").write_text(
        json.dumps([record.model_dump(mode="json") for record in deduped_records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "screening_decisions.json").write_text(
        json.dumps([decision.model_dump(mode="json") for decision in decisions], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_dir
