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
from literature_screening.core.models import ScreeningDecision
from literature_screening.formal_report.fallback import build_fallback_literature_cards
from literature_screening.formal_report.fallback import build_fallback_report_overview
from literature_screening.formal_report.models import CardScreeningInfo
from literature_screening.formal_report.models import ClassificationInfo
from literature_screening.formal_report.models import ContentSummary
from literature_screening.formal_report.models import LiteratureCard
from literature_screening.formal_report.models import ReportingFlags
from literature_screening.formal_report.models import SourceRecord
from literature_screening.formal_report.renderer import render_formal_report_markdown


def test_fallback_card_generation_creates_readable_chinese_fields() -> None:
    paper = PaperRecord(
        paper_id="paper_000001",
        title="Design and modeling of a dual-archimedes screw deep drilling system for lunar subsurface exploration",
        authors=["Alice", "Bob"],
        year=2025,
        journal="Acta Astronautica",
        doi="10.1000/example",
        abstract="This study designs a dual-auger deep drilling system for lunar subsurface exploration and evaluates drilling stability.",
        keywords=["deep drilling", "dual auger", "lunar exploration"],
    )
    decision = ScreeningDecision.model_validate(
        {
            "paper_id": "paper_000001",
            "batch_id": "batch_0001",
            "decision": "include",
            "reason": "标题和摘要显示该研究直接关注月壤环境下的钻进系统设计。",
            "evidence": ["title", "abstract"],
            "confidence": 0.92,
            "screen_stage": "title_abstract",
            "model_provider": "kimi",
            "model_name": "moonshot-v1-auto",
            "timestamp": "2026-03-20T18:00:00+08:00",
        }
    )

    cards = build_fallback_literature_cards([(paper, decision)])

    assert len(cards) == 1
    assert cards[0].classification.primary_category in {"钻进与螺旋推进", "介质响应与相互作用"}
    assert "这篇文献之所以值得保留" in cards[0].content_summary.value_for_topic
    assert cards[0].reporting_flags.recommended_level == "high"


def test_renderer_uses_original_titles_in_headings_and_appendix(tmp_path: Path) -> None:
    card = LiteratureCard(
        paper_id="paper_000001",
        source_record=SourceRecord(
            title_en="Original English Title",
            title_zh="中文译名",
            authors=["Alice", "Bob"],
            year=2025,
            journal="Journal",
            doi="10.1000/example",
            abstract="Abstract",
        ),
        screening_info=CardScreeningInfo(
            decision="include",
            screen_stage="title_abstract",
            reason="reason",
            confidence=0.9,
        ),
        content_summary=ContentSummary(
            one_sentence_summary="一句话概括。",
            core_summary="核心总结。",
            research_focus="研究重点。",
            value_for_topic="参考价值。",
            limitations="局限性。",
        ),
        classification=ClassificationInfo(
            primary_category="测试分类",
            secondary_category=None,
            study_type="实验研究",
            application_context=None,
            core_problem="核心问题。",
            method_keywords=["关键词"],
            domain_tags=["标签"],
        ),
        reporting_flags=ReportingFlags(recommended_level="high", is_key_paper=True),
    )
    overview = build_fallback_report_overview([card], "测试主题")
    output_path = tmp_path / "formal_report.md"

    render_formal_report_markdown(overview, [card], output_path)

    text = output_path.read_text(encoding="utf-8")
    assert "Original English Title" in text
    assert "中文译名" in text
    assert "| 1 | Original English Title |" in text
