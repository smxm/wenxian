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
from literature_screening.core.models import ScreeningDecision
from literature_screening.formal_report.fallback import build_fallback_literature_cards
from literature_screening.formal_report.reference_list import build_reference_block
from literature_screening.formal_report.simple_report import SimplePaperNote
from literature_screening.formal_report.simple_report import SimpleReportCategory
from literature_screening.formal_report.simple_report import SimpleReportOverview
from literature_screening.formal_report.simple_report import _build_overview_prompt
from literature_screening.formal_report.simple_report import _build_total_summary
from literature_screening.formal_report.simple_report import _infer_simple_category_hint
from literature_screening.formal_report.simple_report import _normalize_overview
from literature_screening.formal_report.simple_report import _normalize_simple_category
from literature_screening.formal_report.simple_report import generate_simple_report
from literature_screening.formal_report.simple_report import render_simple_report_markdown


def test_build_fallback_literature_cards_classifies_humanities_topics() -> None:
    rows = [
        (
            PaperRecord(
                paper_id="paper_1",
                title="女性主义视域下《安娜·卡列尼娜》的死亡意象分析",
                abstract="文章从女性主义角度讨论安娜悲剧命运与死亡意象。",
                keywords=["女性主义", "死亡意象"],
            ),
            ScreeningDecision(
                paper_id="paper_1",
                batch_id="batch_1",
                decision="include",
                reason="relevant",
                confidence=0.9,
                model_provider="system",
                model_name="dataset-loader",
                timestamp="2026-04-16T00:00:00+08:00",
            ),
        ),
        (
            PaperRecord(
                paper_id="paper_2",
                title="凝视理论视域下安娜·卡列尼娜的悲剧探析",
                abstract="聚焦凝视与目光困境。",
                keywords=["凝视", "目光"],
            ),
            ScreeningDecision(
                paper_id="paper_2",
                batch_id="batch_1",
                decision="include",
                reason="relevant",
                confidence=0.9,
                model_provider="system",
                model_name="dataset-loader",
                timestamp="2026-04-16T00:00:00+08:00",
            ),
        ),
        (
            PaperRecord(
                paper_id="paper_3",
                title="安娜·卡列尼娜与娜拉的比较分析",
                abstract="通过比较安娜与娜拉讨论女性觉醒。",
                keywords=["比较", "娜拉"],
            ),
            ScreeningDecision(
                paper_id="paper_3",
                batch_id="batch_1",
                decision="include",
                reason="relevant",
                confidence=0.9,
                model_provider="system",
                model_name="dataset-loader",
                timestamp="2026-04-16T00:00:00+08:00",
            ),
        ),
        (
            PaperRecord(
                paper_id="paper_4",
                title="重塑安娜：列夫·托尔斯泰与玛格丽特·杜拉斯的伦理选择",
                abstract="文章讨论自由意志与伦理选择的冲突。",
                keywords=["伦理选择", "自由意志"],
            ),
            ScreeningDecision(
                paper_id="paper_4",
                batch_id="batch_1",
                decision="include",
                reason="relevant",
                confidence=0.9,
                model_provider="system",
                model_name="dataset-loader",
                timestamp="2026-04-16T00:00:00+08:00",
            ),
        ),
    ]

    cards = build_fallback_literature_cards(rows)

    assert [card.classification.primary_category for card in cards] == [
        "女性主义视角下的悲剧分析",
        "凝视、他者与意识形态批评",
        "比较文学与女性形象研究",
        "自由意志与主体性困境",
    ]


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

    assert (
        '<div id="refs"' in markdown
        or "[1] Huang X, & He J. (2026). Original Title A. Journal A, 12(3), 100-110." in markdown
    )
    if '<div id="refs"' in markdown:
        assert "<em>Journal A</em>" in markdown
        assert "[1]" not in markdown
    assert "https://doi.org/10.1000/example-a" in markdown


def test_render_simple_report_markdown_uses_structured_page_fields_when_raw_bibtex_missing() -> None:
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
        overall_summary="The report focuses on structured metadata.",
        categories=[SimpleReportCategory(name="Experiment", intro="Structured metadata is preserved.", paper_ids=["paper_1"])],
    )
    records = [
        PaperRecord(
            paper_id="paper_1",
            title="Original Title A",
            authors=["Huang X", "He J"],
            year=2026,
            journal="Journal A",
            volume="12",
            number="3",
            pages="100-110",
        )
    ]

    markdown = render_simple_report_markdown(
        project_topic="Test Topic",
        notes=notes,
        overview=overview,
        records=records,
    )

    assert "[1] Huang X, He J. Original Title A[J]. Journal A, 2026, 12(3): 100-110." in markdown


def test_build_total_summary_handles_empty_note_list() -> None:
    summary = _build_total_summary(project_topic="Test Topic", ordered_groups=[])

    assert "暂未形成可供整理的纳入文献" in summary
    assert "Test Topic" in summary


def test_build_overview_prompt_does_not_leak_local_category_hints(tmp_path: Path) -> None:
    prompt_path = tmp_path / "overview_prompt.md"
    prompt_path.write_text("{{ input_payload }}\n{{ output_schema }}", encoding="utf-8")
    notes = [
        SimplePaperNote(
            paper_id="paper_1",
            title="Share pledge and earnings persistence",
            category="机器人控制与作业辅助",
            summary="该研究探讨股权质押对企业盈利持续性的影响。",
            analysis="可用于分析企业治理风险与盈利持续性。",
        )
    ]

    prompt = _build_overview_prompt(prompt_path=prompt_path, project_topic="ROE and earnings persistence", notes=notes)

    assert "Share pledge and earnings persistence" in prompt
    assert "category_hint" not in prompt
    assert "机器人控制与作业辅助" not in prompt


def test_simple_report_category_hint_uses_domain_neutral_labels() -> None:
    paper = PaperRecord(
        paper_id="paper_1",
        title="Share pledge and earnings persistence: evidence from China",
        abstract="This paper studies the effect of share pledges on earnings persistence and the mechanism that explains the effect.",
        keywords=["Share pledge", "earnings persistence", "corporate governance"],
    )
    decision = ScreeningDecision(
        paper_id="paper_1",
        batch_id="batch_1",
        decision="include",
        reason="Selected from reusable project dataset.",
        confidence=0.9,
        model_provider="system",
        model_name="dataset-loader",
        timestamp="2026-04-24T00:00:00+08:00",
    )

    hint = _infer_simple_category_hint(paper=paper, decision=decision)

    assert hint == "实证检验与影响因素"
    assert _normalize_simple_category("机器人控制与作业辅助") == "主题相关研究"


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
