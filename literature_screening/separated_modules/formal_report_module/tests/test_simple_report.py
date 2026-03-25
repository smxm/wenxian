from __future__ import annotations

import json
import sys
from pathlib import Path


def _bootstrap() -> None:
    module_root = Path(__file__).resolve().parents[1]
    project_root = module_root.parents[1]
    main_src = project_root / "src"
    detached_src = module_root / "src"

    if str(main_src) not in sys.path:
        sys.path.insert(0, str(main_src))

    import literature_screening

    detached_pkg_root = detached_src / "literature_screening"
    if str(detached_pkg_root) not in list(literature_screening.__path__):
        literature_screening.__path__.append(str(detached_pkg_root))


_bootstrap()

from literature_screening.core.models import ModelConfig
from literature_screening.core.models import PaperRecord
from literature_screening.formal_report.reference_list import build_reference_block
from literature_screening.formal_report.simple_report import SimplePaperNote
from literature_screening.formal_report.simple_report import SimpleReportCategory
from literature_screening.formal_report.simple_report import SimpleReportOverview
from literature_screening.formal_report.simple_report import _build_total_summary
from literature_screening.formal_report.simple_report import _normalize_overview
from literature_screening.formal_report.simple_report import generate_simple_report
from literature_screening.formal_report.simple_report import render_simple_report_markdown


def test_render_simple_report_markdown_uses_overview_structure() -> None:
    notes = [
        SimplePaperNote(
            paper_id="paper_1",
            title="Original Title A",
            category="Old Category A",
            summary="This is the first summary.",
            analysis="This is the first analysis.",
        ),
        SimplePaperNote(
            paper_id="paper_2",
            title="Original Title B",
            category="Old Category B",
            summary="This is the second summary.",
            analysis="This is the second analysis.",
        ),
    ]
    overview = SimpleReportOverview(
        overall_summary="The included papers mainly fall into two directions.",
        categories=[
            SimpleReportCategory(
                name="Direction One",
                intro="This category focuses on direction one.",
                paper_ids=["paper_2", "paper_1"],
            )
        ],
    )
    records = [
        PaperRecord(
            paper_id="paper_1",
            title="Original Title A",
            authors=["Huang X", "He J", "Wang H", "Li Y"],
            year=2026,
            journal="Journal A",
            doi="10.1000/example-a",
            raw_bibtex="@ARTICLE{a,\n volume = {12},\n number = {3},\n pages = {100-110},\n}",
        ),
        PaperRecord(
            paper_id="paper_2",
            title="Original Title B",
            authors=["Smith J", "Taylor R"],
            year=2025,
            journal="Journal B",
            doi="10.1000/example-b",
        ),
    ]

    markdown = render_simple_report_markdown(
        project_topic="Test Topic",
        notes=notes,
        overview=overview,
        records=records,
    )

    assert "# 一、相关文献总体情况" in markdown
    assert "The included papers mainly fall into two directions." in markdown
    assert "## Direction One" in markdown
    assert markdown.index("- Original Title B") < markdown.index("- Original Title A")
    assert "## Original Title A" in markdown
    assert "总结：" in markdown
    assert "分析：" in markdown
    assert "# 参考列表" in markdown
    assert "[1] Huang X, He J, Wang H, et al. Original Title A[J]. Journal A, 2026, 12(3): 100-110." in markdown
    assert "DOI: 10.1000/example-a" not in markdown


def test_render_simple_report_markdown_supports_apa7_reference_style(tmp_path: Path) -> None:
    notes = [
        SimplePaperNote(
            paper_id="paper_1",
            title="Original Title A",
            category="Experiment",
            summary="Short summary.",
            analysis="Short analysis.",
        )
    ]
    overview = SimpleReportOverview(
        overall_summary="The report focuses on experimental validation.",
        categories=[SimpleReportCategory(name="Experiment", intro="Papers in this category focus on validation.", paper_ids=["paper_1"])],
    )
    records = [
        PaperRecord(
            paper_id="paper_1",
            title="Original Title A",
            authors=["Huang X", "He J"],
            year=2026,
            journal="Journal A",
            doi="10.1000/example-a",
            raw_bibtex="@ARTICLE{a,\n volume = {12},\n number = {3},\n pages = {100-110},\n}",
        )
    ]
    reference_lines = build_reference_block(records, style="apa7", working_dir=tmp_path)

    markdown = render_simple_report_markdown(
        project_topic="Test Topic",
        notes=notes,
        overview=overview,
        records=records,
        reference_style="apa7",
        reference_lines=reference_lines,
    )

    assert '<div id="refs"' in markdown
    assert "<em>Journal A</em>" in markdown
    assert "https://doi.org/10.1000/example-a" in markdown
    assert "[1]" not in markdown


def test_build_total_summary_handles_empty_note_list() -> None:
    summary = _build_total_summary(project_topic="Test Topic", ordered_groups=[])

    assert "暂未形成可供整理的纳入文献" in summary
    assert "Test Topic" in summary


def test_normalize_overview_assigns_missing_notes() -> None:
    notes = [
        SimplePaperNote(paper_id="paper_1", title="A", category="Alpha", summary="s1", analysis="a1"),
        SimplePaperNote(paper_id="paper_2", title="B", category="Beta", summary="s2", analysis="a2"),
    ]
    overview = SimpleReportOverview(
        overall_summary="",
        categories=[SimpleReportCategory(name="Alpha Group", intro="", paper_ids=["paper_1"])],
    )

    normalized = _normalize_overview(overview=overview, notes=notes, project_topic="Test Topic")

    assert len(normalized.categories) == 2
    assert normalized.categories[1].name == "其他相关文献"
    assert normalized.categories[1].paper_ids == ["paper_2"]


def test_generate_simple_report_reuses_shared_note_cache(monkeypatch, tmp_path: Path) -> None:
    screening_output_dir = tmp_path / "screening_output"
    screening_output_dir.mkdir(parents=True, exist_ok=True)
    report_output_dir_a = tmp_path / "report_a"
    report_output_dir_b = tmp_path / "report_b"
    shared_cache_dir = tmp_path / "shared_cache"

    deduped = [
        {
            "paper_id": "paper_1",
            "entry_type": "article",
            "title": "Paper One",
            "authors": ["Author A"],
            "year": 2024,
            "journal": "Journal A",
            "doi": None,
            "abstract": "Abstract one",
            "keywords": [],
            "normalized_title": None,
            "raw_bibtex": None,
            "source_files": [],
            "source_keys": [],
            "merged_from": [],
            "status": "unprocessed",
        },
        {
            "paper_id": "paper_2",
            "entry_type": "article",
            "title": "Paper Two",
            "authors": ["Author B"],
            "year": 2024,
            "journal": "Journal B",
            "doi": None,
            "abstract": "Abstract two",
            "keywords": [],
            "normalized_title": None,
            "raw_bibtex": None,
            "source_files": [],
            "source_keys": [],
            "merged_from": [],
            "status": "unprocessed",
        },
        {
            "paper_id": "paper_3",
            "entry_type": "article",
            "title": "Paper Three",
            "authors": ["Author C"],
            "year": 2024,
            "journal": "Journal C",
            "doi": None,
            "abstract": "Abstract three",
            "keywords": [],
            "normalized_title": None,
            "raw_bibtex": None,
            "source_files": [],
            "source_keys": [],
            "merged_from": [],
            "status": "unprocessed",
        },
    ]
    (screening_output_dir / "deduped_records.json").write_text(json.dumps(deduped, ensure_ascii=False, indent=2), encoding="utf-8")

    first_decisions = [
        {
            "paper_id": "paper_1",
            "batch_id": "batch_1",
            "decision": "include",
            "reason": "include one",
            "evidence": [],
            "confidence": 0.9,
            "screen_stage": "title_abstract",
            "model_provider": "deepseek",
            "model_name": "deepseek-reasoner",
            "timestamp": "2026-03-25T00:00:00+08:00",
        },
        {
            "paper_id": "paper_2",
            "batch_id": "batch_1",
            "decision": "include",
            "reason": "include two",
            "evidence": [],
            "confidence": 0.9,
            "screen_stage": "title_abstract",
            "model_provider": "deepseek",
            "model_name": "deepseek-reasoner",
            "timestamp": "2026-03-25T00:00:00+08:00",
        },
    ]
    second_decisions = [
        {
            "paper_id": "paper_2",
            "batch_id": "batch_1",
            "decision": "include",
            "reason": "include two",
            "evidence": [],
            "confidence": 0.9,
            "screen_stage": "title_abstract",
            "model_provider": "deepseek",
            "model_name": "deepseek-reasoner",
            "timestamp": "2026-03-25T00:00:00+08:00",
        },
        {
            "paper_id": "paper_3",
            "batch_id": "batch_1",
            "decision": "include",
            "reason": "include three",
            "evidence": [],
            "confidence": 0.9,
            "screen_stage": "title_abstract",
            "model_provider": "deepseek",
            "model_name": "deepseek-reasoner",
            "timestamp": "2026-03-25T00:00:00+08:00",
        },
    ]

    request_calls: list[str] = []

    def fake_request_note_with_retries(*, paper: PaperRecord, **_: object) -> SimplePaperNote:
        request_calls.append(paper.paper_id)
        return SimplePaperNote(
            paper_id=paper.paper_id,
            title=paper.title,
            category="Category",
            summary=f"Summary for {paper.paper_id}",
            analysis=f"Analysis for {paper.paper_id}",
        )

    def fake_request_overview_with_retries(*, notes: list[SimplePaperNote], **_: object) -> SimpleReportOverview:
        return SimpleReportOverview(
            overall_summary="summary",
            categories=[SimpleReportCategory(name="Category", intro="intro", paper_ids=[note.paper_id for note in notes])],
        )

    monkeypatch.setattr("literature_screening.formal_report.simple_report._request_note_with_retries", fake_request_note_with_retries)
    monkeypatch.setattr("literature_screening.formal_report.simple_report._request_overview_with_retries", fake_request_overview_with_retries)

    model_config = ModelConfig(
        provider="deepseek",
        model_name="deepseek-reasoner",
        api_base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",
    )

    (screening_output_dir / "screening_decisions.json").write_text(json.dumps(first_decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    generate_simple_report(
        screening_output_dir=screening_output_dir,
        report_output_dir=report_output_dir_a,
        shared_notes_cache_dir=shared_cache_dir,
        project_topic="Topic",
        model_config=model_config,
    )
    assert request_calls == ["paper_1", "paper_2"]

    request_calls.clear()
    (screening_output_dir / "screening_decisions.json").write_text(json.dumps(second_decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    generate_simple_report(
        screening_output_dir=screening_output_dir,
        report_output_dir=report_output_dir_b,
        shared_notes_cache_dir=shared_cache_dir,
        project_topic="Topic",
        model_config=model_config,
    )

    assert request_calls == ["paper_3"]
    second_notes = json.loads((report_output_dir_b / "paper_notes.json").read_text(encoding="utf-8"))
    assert [item["paper_id"] for item in second_notes] == ["paper_2", "paper_3"]
