from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_SRC = PROJECT_ROOT / "src"
DETACHED_MODULE_ROOT = PROJECT_ROOT / "separated_modules" / "formal_report_module"
DETACHED_SRC = DETACHED_MODULE_ROOT / "src"
UI_RUNS_ROOT = PROJECT_ROOT / "data" / "ui_runs"
SUPPORTED_INPUT_SUFFIXES = {".bib", ".enw", ".ris", ".txt"}


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
    temperature: float = 0.0
    max_tokens: int = 1536
    min_request_interval_seconds: float = 2.0


@dataclass(slots=True)
class ScreeningJobRequest:
    project_name: str
    input_paths: list[Path]
    criteria: CriteriaDraft
    model: ModelDraft
    batch_size: int = 5
    target_include_count: int = 9999
    stop_when_target_reached: bool = False
    allow_uncertain: bool = True
    retry_times: int = 8
    request_timeout_seconds: int = 240
    encoding: str = "utf-8"
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
    timeout_seconds: int = 240
    retry_times: int = 6


@dataclass(slots=True)
class ReportJobResult:
    run_root: Path
    report_output_dir: Path
    report_path: Path
    notes_path: Path
    markdown: str


def parse_criteria_markdown_text(text: str, source_path: str | None = None) -> CriteriaDraft:
    normalized_lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]
    non_empty_lines = [line for line in normalized_lines if line]

    topic = ""
    bracket_match = re.search(r"【([^】]+)】", text)
    if bracket_match:
        topic = bracket_match.group(1).strip()
    if not topic:
        for line in non_empty_lines:
            if line.startswith("#"):
                continue
            if "论文" in line and "关于" in line:
                topic = line
                break
    if not topic:
        topic = "未命名文献主题"

    inclusion = _extract_criteria_items(text, ["纳入标准", "Inclusion Criteria"])
    exclusion = _extract_criteria_items(text, ["排除标准", "Exclusion Criteria"])

    return CriteriaDraft(
        topic=topic,
        inclusion=inclusion or ["请补充纳入标准"],
        exclusion=exclusion or ["请补充排除标准"],
        source_path=source_path,
    )


def scan_supported_input_files(folder: Path) -> list[Path]:
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Input folder not found: {folder}")

    files = [path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_SUFFIXES]
    return sorted(files, key=lambda item: item.name.lower())


def run_screening_job(request: ScreeningJobRequest) -> ScreeningJobResult:
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

    run_slug = _build_run_slug(request.project_name)
    run_root = UI_RUNS_ROOT / run_slug
    input_dir = run_root / "inputs"
    criteria_dir = run_root / "criteria"
    output_dir = run_root / "screening_output"

    input_dir.mkdir(parents=True, exist_ok=True)
    criteria_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    copied_input_paths = _copy_input_files(request.input_paths, input_dir)
    criteria_path = criteria_dir / "criteria.md"
    criteria_path.write_text(_render_criteria_markdown(request.criteria), encoding="utf-8")

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
    config_path = run_root / "generated_screening_config.yaml"
    config_path.write_text(yaml.safe_dump(config_payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    run_config = RunConfig(
        project=ProjectConfig(**config_payload["project"]),
        input=InputConfig(**config_payload["input"]),
        dedup=DedupConfig(**config_payload["dedup"]),
        screening=ScreeningConfig(**config_payload["screening"]),
        criteria=CriteriaConfig(**config_payload["criteria"]),
        model=ModelConfig(**config_payload["model"]),
        report=ReportConfig(**config_payload["report"]),
    )
    run_pipeline(run_config, dry_run=False)

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


def generate_simple_report_job(request: ReportJobRequest) -> ReportJobResult:
    bootstrap_project_paths()

    from literature_screening.core.models import ModelConfig
    from literature_screening.formal_report.simple_report import DEFAULT_SIMPLE_REPORT_FILENAME
    from literature_screening.formal_report.simple_report import generate_simple_report

    report_output_dir = request.screening_output_dir.parent / f"{request.report_name}_output"
    report_output_dir.mkdir(parents=True, exist_ok=True)

    model_config = ModelConfig(
        provider=request.model.provider,
        model_name=request.model.model_name,
        api_base_url=request.model.api_base_url,
        api_key_env=request.model.api_key_env,
        temperature=request.model.temperature,
        max_tokens=request.model.max_tokens,
        min_request_interval_seconds=request.model.min_request_interval_seconds,
    )
    generate_simple_report(
        screening_output_dir=request.screening_output_dir,
        report_output_dir=report_output_dir,
        project_topic=request.project_topic,
        model_config=model_config,
        timeout_seconds=request.timeout_seconds,
        retry_times=request.retry_times,
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
            }
        )
    return rows


def list_ui_runs() -> list[Path]:
    UI_RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    return sorted([path for path in UI_RUNS_ROOT.iterdir() if path.is_dir()], reverse=True)


def load_existing_screening_run(output_dir: Path) -> ScreeningJobResult:
    summary = _load_json(output_dir / "run_summary.json")
    config_path = output_dir.parent / "generated_screening_config.yaml"
    criteria_topic = ""
    project_name = output_dir.parent.name
    if config_path.exists():
        config_payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        project_name = config_payload.get("project", {}).get("name", project_name)
        criteria_topic = config_payload.get("criteria", {}).get("topic", "")

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
        run_slug=output_dir.parent.name,
        run_root=output_dir.parent,
        config_path=config_path,
        output_dir=output_dir,
        summary=summary,
        records=load_screening_records(output_dir),
        reports=reports,
        project_name=project_name,
        criteria_topic=criteria_topic,
        copied_input_paths=[],
    )


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def api_key_available(env_name: str) -> bool:
    bootstrap_project_paths()
    import os

    return bool(os.getenv(env_name))


def load_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def save_uploaded_file_bytes(files: list[tuple[str, bytes]], target_dir: Path) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for name, content in files:
        path = target_dir / Path(name).name
        path.write_bytes(content)
        saved.append(path)
    return saved


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
    slug = slug or "literature-ui-run"
    return f"{timestamp}_{slug}"


def _extract_criteria_items(text: str, labels: list[str]) -> list[str]:
    items: list[str] = []
    for line in text.replace("\r\n", "\n").split("\n"):
        stripped = line.strip().lstrip("*-").strip()
        if not stripped:
            continue
        for label in labels:
            if label in stripped and "：" in stripped:
                tail = stripped.split("：", 1)[1]
                items.extend(_split_criteria_sentence(tail))
            elif label in stripped and ":" in stripped:
                tail = stripped.split(":", 1)[1]
                items.extend(_split_criteria_sentence(tail))
    return [item for item in items if item]


def _split_criteria_sentence(text: str) -> list[str]:
    parts = re.split(r"[；;](?![^()（）]*[)）])", text)
    cleaned = [part.strip(" 。；;") for part in parts if part.strip(" 。；;")]
    return cleaned


def _render_criteria_markdown(criteria: CriteriaDraft) -> str:
    lines = ["# Topic", "", criteria.topic, "", "## Inclusion", ""]
    lines.extend([f"- {item}" for item in criteria.inclusion])
    lines.extend(["", "## Exclusion", ""])
    lines.extend([f"- {item}" for item in criteria.exclusion])
    return "\n".join(lines).strip() + "\n"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
