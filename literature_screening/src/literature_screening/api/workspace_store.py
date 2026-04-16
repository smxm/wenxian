from __future__ import annotations

import hashlib
import json
import re
import shutil
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from literature_screening.bibtex.deduper import deduplicate_records
from literature_screening.bibtex.exporter import export_ris
from literature_screening.bibtex.normalizer import normalize_title
from literature_screening.bibtex.parser import parse_bibtex_files
from literature_screening.core.models import PaperRecord
from literature_screening.storage_paths import rewrite_storage_payload


class WorkspaceStore:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.projects_dir = root_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def create_project(self, *, name: str, topic: str, description: str | None = None) -> dict[str, Any]:
        project_id = uuid.uuid4().hex[:12]
        now = datetime.now().astimezone().isoformat()
        payload = {
            "id": project_id,
            "name": name,
            "topic": topic,
            "description": description or "",
            "thread_profile": {
                "strategy": {
                    "research_need": "",
                    "selected_databases": ["scopus", "wos", "pubmed", "cnki"],
                    "model": None,
                    "latest_task_id": None,
                    "plan": None,
                },
                "screening": {
                    "topic": topic,
                    "criteria_markdown": "",
                    "inclusion": [],
                    "exclusion": [],
                    "model": None,
                    "batch_size": 10,
                    "target_include_count": None,
                    "stop_when_target_reached": False,
                    "allow_uncertain": True,
                    "retry_times": 6,
                    "request_timeout_seconds": 240,
                    "encoding": "auto",
                },
                "last_updated_at": now,
            },
            "created_at": now,
            "updated_at": now,
        }
        project_root = self._project_root(project_id)
        (project_root / "datasets").mkdir(parents=True, exist_ok=True)
        (project_root / "derived").mkdir(parents=True, exist_ok=True)
        self._write(project_root / "project.json", payload)
        return payload

    def list_projects(self) -> list[dict[str, Any]]:
        projects: list[dict[str, Any]] = []
        for path in sorted(self.projects_dir.glob("*/project.json")):
            project = self._read(path)
            project_id = project["id"]
            project["dataset_count"] = len(self.list_project_datasets(project_id))
            projects.append(project)
        projects.sort(key=lambda item: item["updated_at"], reverse=True)
        return projects

    def load_project(self, project_id: str) -> dict[str, Any]:
        return self._read(self._project_root(project_id) / "project.json")

    def update_project(self, project_id: str, **changes: Any) -> dict[str, Any]:
        path = self._project_root(project_id) / "project.json"
        payload = self._read(path)
        payload.update(changes)
        payload["updated_at"] = datetime.now().astimezone().isoformat()
        self._write(path, payload)
        return payload

    def delete_project(self, project_id: str) -> None:
        project_root = self._project_root(project_id)
        if project_root.exists():
            shutil.rmtree(project_root)

    def list_project_datasets(self, project_id: str) -> list[dict[str, Any]]:
        datasets_dir = self._project_root(project_id) / "datasets"
        if not datasets_dir.exists():
            return []
        datasets = [self._read(path) for path in datasets_dir.glob("*.json")]
        datasets.sort(key=lambda item: item["created_at"], reverse=True)
        return datasets

    def load_dataset(self, project_id: str, dataset_id: str) -> dict[str, Any]:
        return self._read(self._project_root(project_id) / "datasets" / f"{dataset_id}.json")

    def find_dataset(self, dataset_id: str) -> dict[str, Any] | None:
        for path in self.projects_dir.glob(f"*/datasets/{dataset_id}.json"):
            return self._read(path)
        return None

    def register_dataset(
        self,
        *,
        project_id: str,
        task_id: str | None,
        kind: str,
        label: str,
        path: Path,
        record_count: int | None,
        file_format: str,
        source_dataset_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        dataset_id: str | None = None,
    ) -> dict[str, Any]:
        dataset_id = dataset_id or uuid.uuid4().hex[:12]
        now = datetime.now().astimezone().isoformat()
        payload = {
            "id": dataset_id,
            "project_id": project_id,
            "task_id": task_id,
            "kind": kind,
            "label": label,
            "path": str(path),
            "filename": path.name,
            "format": file_format,
            "record_count": record_count,
            "source_dataset_ids": source_dataset_ids or [],
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
        }
        dataset_path = self._project_root(project_id) / "datasets" / f"{dataset_id}.json"
        dataset_path.parent.mkdir(parents=True, exist_ok=True)
        self._write(dataset_path, payload)
        self.update_project(project_id)
        return payload

    _INTERNAL_PAPER_ID_PATTERN = re.compile(r"^(raw|paper)_\d{6}$")

    def _looks_like_internal_paper_id(self, value: str | None) -> bool:
        if not value:
            return False
        return bool(self._INTERNAL_PAPER_ID_PATTERN.match(str(value).strip()))

    def _load_task(self, task_id: str) -> dict[str, Any] | None:
        task_path = self.root_dir / "tasks" / task_id / "task.json"
        if not task_path.exists():
            return None
        return self._read(task_path)

    def _load_task_output_dir(self, task_id: str) -> Path | None:
        task = self._load_task(task_id)
        if not task:
            return None
        output_dir = task.get("output_dir")
        if not output_dir:
            return None
        try:
            return Path(output_dir)
        except TypeError:
            return None

    def _load_task_included_records(self, task_id: str) -> list[PaperRecord] | None:
        output_dir = self._load_task_output_dir(task_id)
        if output_dir is None:
            return None

        records_path = output_dir / "deduped_records.json"
        decisions_path = output_dir / "reviewed" / "screening_decisions.reviewed.json"
        if not decisions_path.exists():
            decisions_path = output_dir / "screening_decisions.json"
        if not records_path.exists() or not decisions_path.exists():
            return None

        try:
            record_payload = json.loads(records_path.read_text(encoding="utf-8"))
            decision_payload = json.loads(decisions_path.read_text(encoding="utf-8"))
        except Exception:
            return None

        records = [PaperRecord.model_validate(item) for item in record_payload if isinstance(item, dict)]
        record_map = {record.paper_id: record for record in records}
        included_records: list[PaperRecord] = []
        for decision in decision_payload:
            if not isinstance(decision, dict):
                continue
            if str(decision.get("decision", "")).strip() != "include":
                continue
            paper_id = str(decision.get("paper_id", "")).strip()
            record = record_map.get(paper_id)
            if record is not None:
                included_records.append(record)
        return included_records

    def _collect_included_records_for_dataset(self, project_id: str, dataset: dict[str, Any]) -> list[PaperRecord]:
        if dataset.get("kind") == "cumulative_included":
            collected: list[PaperRecord] = []
            for dataset_id in dataset.get("source_dataset_ids") or []:
                try:
                    source = self.load_dataset(project_id, dataset_id)
                except FileNotFoundError:
                    continue
                collected.extend(self._collect_included_records_for_dataset(project_id, source))
            if collected:
                return collected

        task_id = dataset.get("task_id")
        if task_id:
            included = self._load_task_included_records(str(task_id))
            if included:
                return included

        path = Path(str(dataset.get("path", "")))
        if path.exists():
            return parse_bibtex_files([path], encoding="auto")
        return []

    def rebuild_cumulative_included_dataset(self, project_id: str) -> dict[str, Any] | None:
        all_datasets = [
            item
            for item in self.list_project_datasets(project_id)
            if item["kind"] in {"included", "included_reviewed"}
        ]
        chosen_by_task: dict[str, dict[str, Any]] = {}
        fallback_datasets: list[dict[str, Any]] = []

        for item in sorted(all_datasets, key=lambda entry: entry["created_at"]):
            task_id = item.get("task_id")
            if not task_id:
                fallback_datasets.append(item)
                continue
            current = chosen_by_task.get(task_id)
            if current is None:
                chosen_by_task[task_id] = item
                continue
            if current["kind"] == "included_reviewed":
                if item["kind"] == "included_reviewed":
                    chosen_by_task[task_id] = item
                continue
            if item["kind"] == "included_reviewed" or item["created_at"] >= current["created_at"]:
                chosen_by_task[task_id] = item

        datasets = [*chosen_by_task.values(), *fallback_datasets]
        records: list[PaperRecord] = []
        for dataset in datasets:
            records.extend(self._collect_included_records_for_dataset(project_id, dataset))
        if not records:
            return None

        preserve_ids = any(self._looks_like_internal_paper_id(record.paper_id) for record in records)
        deduped = deduplicate_records(records, preserve_paper_ids=preserve_ids) if preserve_ids else deduplicate_records(records)
        derived_dir = self._project_root(project_id) / "derived"
        derived_dir.mkdir(parents=True, exist_ok=True)
        output_path = derived_dir / "cumulative_included.ris"
        export_ris(deduped, output_path)
        return self.register_dataset(
            project_id=project_id,
            task_id=None,
            kind="cumulative_included",
            label="Cumulative included records",
            path=output_path,
            record_count=len(deduped),
            file_format="ris",
            source_dataset_ids=[item["id"] for item in datasets],
            metadata={"generated": True},
            dataset_id="cumulative-included",
        )

    _WORKBENCH_VERSION = 2
    _WORKBENCH_FILENAME = "workbench_candidates.json"
    _FULLTEXT_READY_DATASET_ID = "fulltext-ready"
    _REPORT_SOURCE_DATASET_ID = "report-source"

    def _workbench_path(self, project_id: str) -> Path:
        return self._project_root(project_id) / "derived" / self._WORKBENCH_FILENAME

    def load_workbench(self, project_id: str) -> dict[str, Any]:
        path = self._workbench_path(project_id)
        if not path.exists():
            return {
                "version": self._WORKBENCH_VERSION,
                "generated_at": None,
                "source_dataset_ids": [],
                "items": [],
            }
        payload = self._read(path)
        if not isinstance(payload, dict):
            return {
                "version": self._WORKBENCH_VERSION,
                "generated_at": None,
                "source_dataset_ids": [],
                "items": [],
            }
        normalized = {
            "version": int(payload.get("version", self._WORKBENCH_VERSION) or self._WORKBENCH_VERSION),
            "generated_at": payload.get("generated_at"),
            "source_dataset_ids": list(payload.get("source_dataset_ids") or []),
            "items": list(payload.get("items") or []),
        }
        return self._reconcile_loaded_workbench(project_id, normalized)

    def save_workbench(self, project_id: str, payload: dict[str, Any]) -> None:
        path = self._workbench_path(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write(path, payload)

    def patch_workbench_items(self, project_id: str, candidate_ids: list[str], changes: dict[str, Any]) -> dict[str, Any]:
        workbench = self.load_workbench(project_id)
        if not candidate_ids:
            return workbench
        candidate_set = set(candidate_ids)
        now = datetime.now().astimezone().isoformat()
        for item in workbench.get("items", []):
            if item.get("candidate_id") not in candidate_set:
                continue
            for key, value in changes.items():
                if value is None:
                    continue
                item[key] = value.strip() if isinstance(value, str) else value
            item["updated_at"] = now
        self.save_workbench(project_id, workbench)
        return self.rebuild_workbench(project_id, source_dataset_ids=workbench.get("source_dataset_ids") or [])

    def update_fulltext_status(
        self,
        *,
        project_id: str,
        paper_id: str,
        status: str,
        note: str | None = None,
        landing_url: str | None = None,
        pdf_url: str | None = None,
        oa_status: str | None = None,
    ) -> dict[str, Any]:
        changes: dict[str, Any] = {}
        if status == "excluded":
            changes["final_decision"] = "exclude"
            if note is not None:
                changes["final_note"] = note
        else:
            changes["access_status"] = status
            if note is not None:
                changes["access_note"] = note
        if landing_url is not None:
            changes["manual_preferred_url"] = landing_url
        if pdf_url is not None:
            changes["manual_pdf_url"] = pdf_url
        if oa_status is not None:
            changes["oa_status"] = oa_status
        candidate_ids = self._resolve_candidate_ids(project_id, [paper_id])
        rebuilt = self.patch_workbench_items(project_id, candidate_ids, changes)
        for item in rebuilt.get("items", []):
            if item.get("candidate_id") in candidate_ids or self._legacy_workbench_identifier(item) == paper_id:
                return item
        return {}

    def load_fulltext_statuses(self, project_id: str) -> dict[str, Any]:
        queue = self.load_fulltext_queue(project_id)
        statuses: dict[str, Any] = {}
        for item in queue.get("items", []):
            statuses[item["paper_id"]] = {
                "status": item.get("status", "pending"),
                "note": item.get("note", ""),
                "landing_url": item.get("landing_url"),
                "pdf_url": item.get("pdf_url"),
                "oa_status": item.get("oa_status"),
                "updated_at": item.get("updated_at"),
            }
        return statuses

    def save_fulltext_statuses(self, project_id: str, payload: dict[str, Any]) -> None:
        workbench = self.load_workbench(project_id)
        if not payload:
            self.save_workbench(project_id, workbench)
            return
        changes_by_candidate: dict[str, dict[str, Any]] = {}
        for identifier, state in payload.items():
            if not isinstance(state, dict):
                continue
            changes: dict[str, Any] = {}
            status = state.get("status")
            note = state.get("note")
            if status == "excluded":
                changes["final_decision"] = "exclude"
                if note is not None:
                    changes["final_note"] = note
            elif status is not None:
                changes["access_status"] = status
                if note is not None:
                    changes["access_note"] = note
            if "landing_url" in state:
                changes["manual_preferred_url"] = state.get("landing_url")
            if "pdf_url" in state:
                changes["manual_pdf_url"] = state.get("pdf_url")
            if "oa_status" in state:
                changes["oa_status"] = state.get("oa_status")
            for candidate_id in self._resolve_candidate_ids(project_id, [identifier]):
                changes_by_candidate[candidate_id] = changes
        now = datetime.now().astimezone().isoformat()
        for item in workbench.get("items", []):
            candidate_id = item.get("candidate_id")
            if candidate_id not in changes_by_candidate:
                continue
            for key, value in changes_by_candidate[candidate_id].items():
                if value is not None:
                    item[key] = value
            item["updated_at"] = now
        self.save_workbench(project_id, workbench)
        self.rebuild_workbench(project_id, source_dataset_ids=workbench.get("source_dataset_ids") or [])

    def load_fulltext_queue(self, project_id: str) -> dict[str, Any]:
        return self._workbench_to_legacy_queue(self.load_workbench(project_id))

    def rebuild_fulltext_queue(
        self,
        project_id: str,
        *,
        source_dataset_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        rebuilt = self.rebuild_workbench(project_id, source_dataset_ids=source_dataset_ids)
        return self._workbench_to_legacy_queue(rebuilt)

    def rebuild_workbench(
        self,
        project_id: str,
        *,
        source_dataset_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        if not source_dataset_ids:
            self.rebuild_cumulative_included_dataset(project_id)

        datasets = self.list_project_datasets(project_id)
        if source_dataset_ids:
            selected = [item for item in datasets if item["id"] in source_dataset_ids]
        else:
            selected = [item for item in datasets if item["kind"] == "cumulative_included"]
            if not selected:
                selected = [item for item in datasets if item["kind"] in {"included_reviewed", "included"}]
                selected.sort(key=lambda item: item["created_at"])
                if selected:
                    selected = [selected[-1]]

        selected_ids = [item["id"] for item in selected]
        previous = self.load_workbench(project_id)
        previous_by_candidate = {
            str(item.get("candidate_id")): item
            for item in previous.get("items", [])
            if isinstance(item, dict) and item.get("candidate_id")
        }
        if not previous_by_candidate:
            previous_by_candidate = self._migrate_legacy_workbench_state(project_id)

        source_entries: list[dict[str, Any]] = []
        records: list[PaperRecord] = []
        for dataset in selected:
            dataset_records = self._collect_included_records_for_dataset(project_id, dataset)
            for record in dataset_records:
                records.append(record)
                source_entries.append(
                    {
                        "record": record,
                        "paper_id": record.paper_id,
                        "dataset_id": dataset["id"],
                        "dataset_label": dataset.get("label"),
                        "task_id": dataset.get("task_id"),
                    }
                )

        derived_dir = self._project_root(project_id) / "derived"
        derived_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now().astimezone().isoformat()
        if not records:
            payload = {
                "version": self._WORKBENCH_VERSION,
                "generated_at": now,
                "source_dataset_ids": selected_ids,
                "items": [],
            }
            self.save_workbench(project_id, payload)
            self._write_report_datasets(project_id, selected_ids, [], [])
            self.update_project(project_id)
            return payload

        canonical_records = deduplicate_records([PaperRecord.model_validate(record.model_dump()) for record in records])
        canonical_by_key = self._build_canonical_record_map(canonical_records)
        source_refs_by_fingerprint: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for entry in source_entries:
            record = entry["record"]
            canonical = self._match_canonical_record(record, canonical_by_key)
            if canonical is None:
                continue
            fingerprint = self._candidate_fingerprint(canonical)
            source_refs_by_fingerprint[fingerprint].append(
                {
                    "paper_id": entry.get("paper_id"),
                    "dataset_id": entry["dataset_id"],
                    "dataset_label": entry.get("dataset_label"),
                    "task_id": entry.get("task_id"),
                }
            )

        items: list[dict[str, Any]] = []
        ready_records: list[PaperRecord] = []
        report_records: list[PaperRecord] = []
        latest_screening_context = self._latest_project_screening_context(project_id)
        for record in canonical_records:
            fingerprint = self._candidate_fingerprint(record)
            candidate_id = self._candidate_id_for_fingerprint(fingerprint)
            previous_state = previous_by_candidate.get(candidate_id, {})
            refs = source_refs_by_fingerprint.get(fingerprint, [])
            item = self._build_workbench_item(
                record=record,
                candidate_id=candidate_id,
                fingerprint=fingerprint,
                previous_state=previous_state,
                source_refs=refs,
                updated_at=previous_state.get("updated_at") or now,
            )
            items.append(item)
            latest_screening_decision = self._latest_screening_decision_for_record(record, latest_screening_context)
            if item.get("access_status") == "ready" and latest_screening_decision not in {"exclude", "uncertain"}:
                ready_records.append(record)
            if (
                item.get("access_status") == "ready"
                and item.get("final_decision") == "include"
                and latest_screening_decision not in {"exclude", "uncertain"}
            ):
                report_records.append(record)

        payload = {
            "version": self._WORKBENCH_VERSION,
            "generated_at": now,
            "source_dataset_ids": selected_ids,
            "items": items,
        }
        self.save_workbench(project_id, payload)
        self._write_report_datasets(project_id, selected_ids, ready_records, report_records)
        self.update_project(project_id)
        return payload

    def _write_report_datasets(
        self,
        project_id: str,
        source_dataset_ids: list[str],
        ready_records: list[PaperRecord],
        report_records: list[PaperRecord],
    ) -> None:
        derived_dir = self._project_root(project_id) / "derived"
        ready_path = derived_dir / "fulltext_ready.ris"
        report_path = derived_dir / "report_source.ris"
        export_ris(ready_records, ready_path)
        export_ris(report_records, report_path)
        self.register_dataset(
            project_id=project_id,
            task_id=None,
            kind="fulltext_ready",
            label="Fulltext ready records",
            path=ready_path,
            record_count=len(ready_records),
            file_format="ris",
            source_dataset_ids=source_dataset_ids,
            metadata={"generated": True},
            dataset_id=self._FULLTEXT_READY_DATASET_ID,
        )
        self.register_dataset(
            project_id=project_id,
            task_id=None,
            kind="report_source",
            label="Report source records",
            path=report_path,
            record_count=len(report_records),
            file_format="ris",
            source_dataset_ids=source_dataset_ids,
            metadata={"generated": True},
            dataset_id=self._REPORT_SOURCE_DATASET_ID,
        )

    def _build_workbench_item(
        self,
        *,
        record: PaperRecord,
        candidate_id: str,
        fingerprint: str,
        previous_state: dict[str, Any],
        source_refs: list[dict[str, Any]],
        updated_at: str,
    ) -> dict[str, Any]:
        access_status = str(previous_state.get("access_status") or "pending")
        final_decision = str(previous_state.get("final_decision") or "undecided")
        if final_decision not in {"undecided", "include", "exclude", "deferred"}:
            final_decision = "undecided"
        if access_status not in {"pending", "ready", "unavailable", "deferred"}:
            access_status = "pending"

        links, preferred_open_url, preferred_pdf_url = self._build_candidate_links(record, previous_state)
        dataset_ids = [str(ref.get("dataset_id")) for ref in source_refs if ref.get("dataset_id")]
        dataset_labels = [str(ref.get("dataset_label")) for ref in source_refs if ref.get("dataset_label")]
        task_ids = [str(ref.get("task_id")) for ref in source_refs if ref.get("task_id")]
        source_record_refs = [
            {
                "paper_id": str(ref.get("paper_id")),
                "task_id": ref.get("task_id"),
                "dataset_id": ref.get("dataset_id"),
                "dataset_label": ref.get("dataset_label"),
            }
            for ref in source_refs
            if str(ref.get("paper_id") or "").strip()
        ]

        return {
            "candidate_id": candidate_id,
            "fingerprint": fingerprint,
            "title": record.title,
            "year": record.year,
            "journal": record.journal,
            "doi": record.doi,
            "source_url": record.url,
            "language": self._detect_language(record),
            "access_status": access_status,
            "final_decision": final_decision,
            "access_note": str(previous_state.get("access_note") or ""),
            "final_note": str(previous_state.get("final_note") or ""),
            "manual_preferred_url": previous_state.get("manual_preferred_url"),
            "manual_pdf_url": previous_state.get("manual_pdf_url"),
            "oa_status": previous_state.get("oa_status"),
            "oa_landing_url": previous_state.get("oa_landing_url"),
            "oa_pdf_url": previous_state.get("oa_pdf_url"),
            "preferred_open_url": preferred_open_url,
            "preferred_pdf_url": preferred_pdf_url,
            "links": links,
            "source_record_refs": source_record_refs,
            "source_dataset_ids": list(dict.fromkeys(dataset_ids)),
            "source_dataset_labels": list(dict.fromkeys(dataset_labels)),
            "source_task_ids": list(dict.fromkeys(task_ids)),
            "updated_at": updated_at,
        }

    def _build_candidate_links(
        self,
        record: PaperRecord,
        state: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str | None, str | None]:
        return self._build_candidate_links_from_values(doi=record.doi, source_url=record.url, state=state)

    def _build_candidate_links_from_values(
        self,
        *,
        doi: Any,
        source_url: Any,
        state: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str | None, str | None]:
        links: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        def push(kind: str, label: str, url: str | None, source: str) -> None:
            if not url:
                return
            cleaned = str(url).strip()
            if not cleaned or cleaned in seen_urls:
                return
            seen_urls.add(cleaned)
            links.append(
                {
                    "kind": kind,
                    "label": label,
                    "url": cleaned,
                    "source": source,
                    "primary": False,
                }
            )

        doi_url = f"https://doi.org/{doi}" if doi else None
        manual_open_url = self._clean_optional_url(state.get("manual_preferred_url"))
        manual_pdf_url = self._clean_optional_url(state.get("manual_pdf_url"))
        source_url = self._clean_optional_url(source_url)
        oa_landing_url = self._clean_optional_url(state.get("oa_landing_url"))
        oa_pdf_url = self._clean_optional_url(state.get("oa_pdf_url"))

        push("manual", "手工首选链接", manual_open_url, "manual")
        push("source", "导入来源链接", source_url, "source")
        push("doi", "DOI", doi_url, "doi")
        push("oa-landing", "OA 落地页", oa_landing_url, "openalex")
        push("manual-pdf", "手工 PDF", manual_pdf_url, "manual")
        push("pdf", "OA PDF", oa_pdf_url, "openalex")

        preferred_open_url = manual_open_url or source_url or doi_url or oa_landing_url or manual_pdf_url or oa_pdf_url
        preferred_pdf_url = manual_pdf_url or oa_pdf_url
        for item in links:
            if preferred_open_url and item["url"] == preferred_open_url:
                item["primary"] = True
                break
        return links, preferred_open_url, preferred_pdf_url

    def _migrate_legacy_workbench_state(self, project_id: str) -> dict[str, dict[str, Any]]:
        queue_path = self._project_root(project_id) / "derived" / "fulltext_queue.json"
        statuses_path = self._project_root(project_id) / "derived" / "fulltext_statuses.json"
        if not queue_path.exists():
            return {}

        queue_payload = self._read(queue_path)
        queue_items = queue_payload.get("items", []) if isinstance(queue_payload, dict) else []
        status_payload = self._read(statuses_path) if statuses_path.exists() else {}
        migrated: dict[str, dict[str, Any]] = {}
        for item in queue_items:
            if not isinstance(item, dict):
                continue
            fingerprint = self._candidate_fingerprint_from_values(
                title=item.get("title"),
                doi=item.get("doi"),
                year=item.get("year"),
                journal=item.get("journal"),
            )
            if not fingerprint:
                continue
            candidate_id = self._candidate_id_for_fingerprint(fingerprint)
            merged_state = {}
            merged_state.update(item)
            raw_status = status_payload.get(item.get("paper_id"), {})
            if isinstance(raw_status, dict):
                merged_state.update(raw_status)
            state: dict[str, Any] = {}
            status = str(merged_state.get("status") or "pending")
            note = str(merged_state.get("note") or "")
            if status == "excluded":
                state["final_decision"] = "exclude"
                if note:
                    state["final_note"] = note
            else:
                state["access_status"] = status if status in {"pending", "ready", "unavailable", "deferred"} else "pending"
                if note:
                    state["access_note"] = note
            if merged_state.get("oa_status"):
                state["oa_status"] = merged_state.get("oa_status")
            landing_url = self._clean_optional_url(merged_state.get("landing_url"))
            pdf_url = self._clean_optional_url(merged_state.get("pdf_url"))
            if self._legacy_url_matches_candidate(
                landing_url,
                doi=item.get("doi"),
                source_url=item.get("source_url"),
            ):
                state["manual_preferred_url"] = landing_url
            if self._legacy_url_matches_candidate(
                pdf_url,
                doi=item.get("doi"),
                source_url=item.get("source_url"),
            ):
                state["manual_pdf_url"] = pdf_url
            if merged_state.get("updated_at"):
                state["updated_at"] = merged_state.get("updated_at")
            migrated[candidate_id] = state
        return migrated

    def _reconcile_loaded_workbench(self, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        items = payload.get("items", [])
        if not items:
            return payload

        legacy_states = self._migrate_legacy_workbench_state(project_id)
        if not legacy_states:
            return payload

        changed = False
        reconciled_items: list[dict[str, Any]] = []
        for raw_item in items:
            if not isinstance(raw_item, dict):
                reconciled_items.append(raw_item)
                continue
            item = dict(raw_item)
            legacy_state = legacy_states.get(str(item.get("candidate_id") or ""))
            if not legacy_state:
                reconciled_items.append(item)
                continue
            item_changed = False

            current_access = str(item.get("access_status") or "pending")
            legacy_access = str(legacy_state.get("access_status") or "")
            if current_access == "pending" and legacy_access in {"ready", "unavailable", "deferred"}:
                item["access_status"] = legacy_access
                item_changed = True

            current_final = str(item.get("final_decision") or "undecided")
            legacy_final = str(legacy_state.get("final_decision") or "")
            if current_final == "undecided" and legacy_final in {"include", "exclude", "deferred"}:
                item["final_decision"] = legacy_final
                item_changed = True

            for field in (
                "access_note",
                "final_note",
                "manual_preferred_url",
                "manual_pdf_url",
                "oa_status",
                "oa_landing_url",
                "oa_pdf_url",
            ):
                current_value = item.get(field)
                legacy_value = legacy_state.get(field)
                if current_value not in (None, "") or legacy_value in (None, ""):
                    continue
                item[field] = legacy_value
                item_changed = True

            if item_changed and legacy_state.get("updated_at") and not item.get("updated_at"):
                item["updated_at"] = legacy_state.get("updated_at")
            if item_changed:
                links, preferred_open_url, preferred_pdf_url = self._build_candidate_links_from_values(
                    doi=item.get("doi"),
                    source_url=item.get("source_url"),
                    state=item,
                )
                item["links"] = links
                item["preferred_open_url"] = preferred_open_url
                item["preferred_pdf_url"] = preferred_pdf_url

            changed = changed or item_changed
            reconciled_items.append(item)

        if not changed:
            return payload

        reconciled = {
            "version": int(payload.get("version", self._WORKBENCH_VERSION) or self._WORKBENCH_VERSION),
            "generated_at": payload.get("generated_at"),
            "source_dataset_ids": list(payload.get("source_dataset_ids") or []),
            "items": reconciled_items,
        }
        self.save_workbench(project_id, reconciled)
        return reconciled

    def _legacy_url_matches_candidate(self, url: str | None, *, doi: Any, source_url: Any) -> bool:
        if not url:
            return False
        cleaned_source = self._clean_optional_url(source_url)
        if cleaned_source and url == cleaned_source:
            return True
        normalized_doi = self._normalized_doi(doi)
        if normalized_doi and self._url_mentions_doi(url, normalized_doi):
            return True
        return cleaned_source is None and normalized_doi is None

    def _clean_optional_url(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _url_mentions_doi(self, url: str, normalized_doi: str) -> bool:
        haystack = unquote(url).lower()
        return normalized_doi in haystack

    def _build_canonical_record_map(self, records: list[PaperRecord]) -> dict[str, PaperRecord]:
        mapping: dict[str, PaperRecord] = {}
        for record in records:
            for key in self._record_match_keys(record):
                mapping.setdefault(key, record)
        return mapping

    def _match_canonical_record(self, record: PaperRecord, canonical_by_key: dict[str, PaperRecord]) -> PaperRecord | None:
        for key in self._record_match_keys(record):
            if key in canonical_by_key:
                return canonical_by_key[key]
        return None

    def _record_match_keys(self, record: PaperRecord) -> list[str]:
        return self._candidate_match_keys(
            title=record.title,
            doi=record.doi,
            year=record.year,
            journal=record.journal,
        )

    def _candidate_match_keys(self, *, title: Any, doi: Any, year: Any, journal: Any) -> list[str]:
        keys: list[str] = []
        normalized_doi = self._normalized_doi(doi)
        if normalized_doi:
            keys.append(f"doi:{normalized_doi}")
        normalized_title = normalize_title(str(title).strip()) if title else ""
        year_text = str(year).strip() if year not in (None, "") else ""
        normalized_journal = normalize_title(str(journal).strip()) if journal else ""
        if normalized_title and year_text:
            keys.append(f"title-year:{normalized_title}|{year_text}")
        if normalized_title and normalized_journal:
            keys.append(f"title-journal:{normalized_title}|{normalized_journal}")
        if normalized_title:
            keys.append(f"title:{normalized_title}")
        return keys

    def _load_project_tasks(self, project_id: str) -> list[dict[str, Any]]:
        tasks: list[dict[str, Any]] = []
        for task_path in sorted((self.root_dir / "tasks").glob("*/task.json")):
            task = self._read(task_path)
            if (task.get("project_id") or task.get("metadata", {}).get("project_id")) == project_id:
                tasks.append(task)
        return tasks

    def _latest_project_screening_context(self, project_id: str) -> dict[str, str]:
        tasks = [
            task
            for task in self._load_project_tasks(project_id)
            if task.get("kind") == "screening" and task.get("records")
        ]
        tasks.sort(key=lambda item: (item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        context: dict[str, str] = {}
        for task in tasks:
            for row in task.get("records", []) or []:
                decision = str(row.get("decision") or "").strip()
                if not decision:
                    continue
                for key in self._candidate_match_keys(
                    title=row.get("title"),
                    doi=row.get("doi"),
                    year=row.get("year"),
                    journal=row.get("journal"),
                ):
                    context.setdefault(key, decision)
        return context

    def _latest_screening_decision_for_record(self, record: PaperRecord, context: dict[str, str]) -> str | None:
        for key in self._record_match_keys(record):
            if key in context:
                return context[key]
        return None

    def _candidate_fingerprint(self, record: PaperRecord) -> str:
        return self._candidate_fingerprint_from_values(
            title=record.title,
            doi=record.doi,
            year=record.year,
            journal=record.journal,
        )

    def _candidate_fingerprint_from_values(self, *, title: Any, doi: Any, year: Any, journal: Any) -> str:
        keys = self._candidate_match_keys(title=title, doi=doi, year=year, journal=journal)
        return keys[0] if keys else f"title:{normalize_title(str(title or '').strip())}"

    def _candidate_id_for_fingerprint(self, fingerprint: str) -> str:
        return f"cand_{hashlib.sha1(fingerprint.encode('utf-8')).hexdigest()[:12]}"

    def _legacy_workbench_identifier(self, item: dict[str, Any]) -> str:
        refs = item.get("source_record_refs") or []
        if isinstance(refs, list):
            for ref in refs:
                if not isinstance(ref, dict):
                    continue
                paper_id = str(ref.get("paper_id") or "").strip()
                if paper_id:
                    return paper_id
        candidate_id = str(item.get("candidate_id") or "").strip()
        return candidate_id

    def _resolve_candidate_ids(self, project_id: str, identifiers: list[str]) -> list[str]:
        requested = [str(identifier).strip() for identifier in identifiers if str(identifier).strip()]
        if not requested:
            return []
        workbench = self.load_workbench(project_id)
        matched: list[str] = []
        seen: set[str] = set()
        for item in workbench.get("items", []):
            candidate_id = str(item.get("candidate_id") or "").strip()
            if not candidate_id:
                continue
            aliases = {candidate_id, self._legacy_workbench_identifier(item)}
            refs = item.get("source_record_refs") or []
            if isinstance(refs, list):
                for ref in refs:
                    if not isinstance(ref, dict):
                        continue
                    paper_id = str(ref.get("paper_id") or "").strip()
                    if paper_id:
                        aliases.add(paper_id)
            if aliases.isdisjoint(requested):
                continue
            if candidate_id in seen:
                continue
            seen.add(candidate_id)
            matched.append(candidate_id)
        for identifier in requested:
            if identifier.startswith("cand_") and identifier not in seen:
                matched.append(identifier)
                seen.add(identifier)
        return matched

    def _normalized_doi(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        normalized = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.IGNORECASE)
        return normalized.lower()

    def _detect_language(self, record: PaperRecord) -> str:
        haystack = " ".join([record.title or "", record.journal or "", record.abstract or ""])
        if re.search(r"[\u4e00-\u9fff]", haystack):
            return "zh"
        if re.search(r"[A-Za-z]", haystack):
            return "en"
        return "unknown"

    def _workbench_to_legacy_queue(self, payload: dict[str, Any]) -> dict[str, Any]:
        legacy_id_counts: dict[str, int] = {}
        for item in payload.get("items", []):
            legacy_id = self._legacy_workbench_identifier(item)
            if legacy_id:
                legacy_id_counts[legacy_id] = legacy_id_counts.get(legacy_id, 0) + 1
        items: list[dict[str, Any]] = []
        for item in payload.get("items", []):
            latest_decision = item.get("latest_screening_decision")
            if latest_decision in {"exclude", "uncertain"}:
                continue
            status = item.get("access_status", "pending")
            note = item.get("access_note", "")
            if item.get("final_decision") == "exclude":
                status = "excluded"
                note = item.get("final_note", note)
            legacy_id = self._legacy_workbench_identifier(item)
            display_paper_id = legacy_id if legacy_id_counts.get(legacy_id, 0) == 1 else item.get("candidate_id")
            legacy_item = {
                "paper_id": display_paper_id,
                "candidate_id": item.get("candidate_id"),
                "title": item.get("title"),
                "year": item.get("year"),
                "journal": item.get("journal"),
                "doi": item.get("doi"),
                "confidence": item.get("latest_screening_confidence"),
                "screening_decision": latest_decision,
                "screening_reason": item.get("latest_screening_reason", ""),
                "doi_url": next((link.get("url") for link in item.get("links", []) if link.get("kind") == "doi"), None),
                "landing_url": item.get("preferred_open_url"),
                "pdf_url": item.get("preferred_pdf_url"),
                "oa_status": item.get("oa_status"),
                "status": status,
                "note": note,
                "updated_at": item.get("updated_at"),
            }
            items.append(legacy_item)
        return {
            "source_dataset_ids": list(payload.get("source_dataset_ids") or []),
            "items": items,
        }

    @staticmethod
    def _count_fulltext_statuses(items: list[dict[str, Any]]) -> dict[str, int]:
        counts = {"pending": 0, "ready": 0, "excluded": 0, "unavailable": 0, "deferred": 0}
        for item in items:
            status = item.get("status", "pending")
            counts[status] = counts.get(status, 0) + 1
        return counts

    def _project_root(self, project_id: str) -> Path:
        return self.projects_dir / project_id

    def _read(self, path: Path) -> Any:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return rewrite_storage_payload(payload, storage_root=self.root_dir, mode="hydrate")

    def _write(self, path: Path, payload: Any) -> None:
        serialized = rewrite_storage_payload(payload, storage_root=self.root_dir, mode="dehydrate")
        path.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")
