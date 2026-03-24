from __future__ import annotations

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

from literature_screening.core.models import PaperRecord
from literature_screening.formal_report.reference_list import build_reference_block
from literature_screening.formal_report.simple_report import SimplePaperNote
from literature_screening.formal_report.simple_report import SimpleReportCategory
from literature_screening.formal_report.simple_report import SimpleReportOverview
from literature_screening.formal_report.simple_report import _build_total_summary
from literature_screening.formal_report.simple_report import _normalize_overview
from literature_screening.formal_report.simple_report import render_simple_report_markdown


def test_render_simple_report_markdown_uses_ai_overview_structure() -> None:
    notes = [
        SimplePaperNote(
            paper_id="paper_1",
            title="Original Title A",
            category="旧提示类别A",
            summary="这是第一篇的总结。",
            analysis="这是第一篇的分析。",
        ),
        SimplePaperNote(
            paper_id="paper_2",
            title="Original Title B",
            category="旧提示类别B",
            summary="这是第二篇的总结。",
            analysis="这是第二篇的分析。",
        ),
    ]
    overview = SimpleReportOverview(
        overall_summary="这批文献主要围绕两个方向展开，分别体现了不同的研究切入点。",
        categories=[
            SimpleReportCategory(
                name="方向一",
                intro="这一类文献关注方向一。",
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
        project_topic="测试主题",
        notes=notes,
        overview=overview,
        records=records,
    )

    assert "# 一、相关文献总体情况" in markdown
    assert "这批文献主要围绕两个方向展开" in markdown
    assert "## 方向一" in markdown
    assert markdown.index("- Original Title B") < markdown.index("- Original Title A")
    assert "## Original Title A" in markdown
    assert "总结：" in markdown
    assert "分析：" in markdown
    assert "# 参考列表" in markdown
    assert "格式参考 GB/T 7714" not in markdown
    assert "[1] Huang X, He J, Wang H, et al. Original Title A[J]. Journal A, 2026, 12(3): 100-110." in markdown
    assert "DOI: 10.1000/example-a" not in markdown


def test_render_simple_report_markdown_supports_apa7_reference_style(tmp_path: Path) -> None:
    notes = [
        SimplePaperNote(
            paper_id="paper_1",
            title="Original Title A",
            category="实验验证",
            summary="简要总结。",
            analysis="简要分析。",
        )
    ]
    overview = SimpleReportOverview(
        overall_summary="总体上，这批文献聚焦于实验验证。",
        categories=[SimpleReportCategory(name="实验验证", intro="这一类文献围绕实验验证展开。", paper_ids=["paper_1"])],
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
        project_topic="测试主题",
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
    summary = _build_total_summary(project_topic="测试主题", ordered_groups=[])

    assert "暂未形成可供整理的纳入文献" in summary
    assert "测试主题" in summary


def test_normalize_overview_assigns_missing_notes() -> None:
    notes = [
        SimplePaperNote(paper_id="paper_1", title="A", category="甲", summary="s1", analysis="a1"),
        SimplePaperNote(paper_id="paper_2", title="B", category="乙", summary="s2", analysis="a2"),
    ]
    overview = SimpleReportOverview(
        overall_summary="",
        categories=[SimpleReportCategory(name="甲类", intro="", paper_ids=["paper_1"])],
    )

    normalized = _normalize_overview(overview=overview, notes=notes, project_topic="测试主题")

    assert len(normalized.categories) == 2
    assert normalized.categories[1].name == "其他相关文献"
    assert normalized.categories[1].paper_ids == ["paper_2"]
