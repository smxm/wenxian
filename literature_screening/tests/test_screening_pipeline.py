from __future__ import annotations

from pathlib import Path

import pytest

from literature_screening.bibtex.deduper import deduplicate_records
from literature_screening.bibtex.exporter import export_ris
from literature_screening.bibtex.normalizer import normalize_title
from literature_screening.bibtex.parser import parse_bibtex_files
from literature_screening.core.exceptions import SchemaValidationError
from literature_screening.core.models import CriteriaConfig, PaperRecord
from literature_screening.screening.prompt_builder import build_screening_prompt
from literature_screening.screening.validator import validate_batch_response


def test_normalize_title_collapses_unicode_and_punctuation() -> None:
    assert normalize_title("Self-Burrowing Robot: Design, Test!") == "self burrowing robot design test"
    assert normalize_title("中文标题（测试版）") == "中文标题 测试版"


def test_deduplicate_records_merges_same_doi() -> None:
    first = PaperRecord(
        paper_id="raw_000001",
        title="Paper A",
        authors=["Alice"],
        doi="10.1000/example",
        abstract="short",
        source_files=["a.bib"],
        source_keys=["A"],
    )
    second = PaperRecord(
        paper_id="raw_000002",
        title="Paper A Extended",
        authors=["Alice", "Bob"],
        doi="10.1000/example",
        abstract="a much longer abstract",
        source_files=["b.bib"],
        source_keys=["B"],
    )

    deduped = deduplicate_records([first, second])

    assert len(deduped) == 1
    assert deduped[0].paper_id == "paper_000001"
    assert deduped[0].authors == ["Alice", "Bob"]
    assert deduped[0].abstract == "a much longer abstract"
    assert deduped[0].source_files == ["a.bib", "b.bib"]


def test_parse_cnki_like_bib_supports_cjk_splitters() -> None:
    records = parse_bibtex_files([Path(__file__).parent / "cnki_like.bib"], encoding="utf-8")

    assert len(records) == 2
    assert records[0].title == "基于居民社区参与的智慧社区建设策略——以南京城区为例"
    assert records[0].authors == ["林雨楠", "甄峰", "秦萧"]
    assert records[0].doi == "10.19892/j.cnki.csjz.2017.27.009"
    assert records[1].title == "智慧社区建设居民参与意愿的影响因素研究"
    assert records[1].authors == ["张叶蕊"]
    assert records[1].journal == "广东财经大学"


def test_parse_cnki_like_enw_reads_abstract_and_keywords() -> None:
    records = parse_bibtex_files([Path(__file__).parent / "cnki_like.enw"], encoding="utf-8")

    assert len(records) == 2
    assert records[0].title == "基于居民社区参与的智慧社区建设策略——以南京城区为例"
    assert records[0].authors == ["林雨楠", "甄峰", "秦萧"]
    assert records[0].keywords == ["社区参与", "智慧社区", "现状", "策略"]
    assert records[0].abstract == "本文基于居民社区参与视角分析智慧社区建设策略。"
    assert records[1].title == "智慧社区建设居民参与意愿的影响因素研究"
    assert records[1].authors == ["张叶蕊"]
    assert records[1].abstract == "本研究讨论智慧社区建设中的居民参与意愿问题。"


def test_parse_ris_article_reads_core_fields() -> None:
    records = parse_bibtex_files([Path(__file__).parent / "article_sample.ris"], encoding="utf-8")

    assert len(records) == 1
    assert records[0].entry_type == "article"
    assert records[0].title == "Comparison of Burrowing-Out Performance and Efficiency Between Dual-Anchor and Extension-Contraction Soft Robots"
    assert records[0].authors == ["Huang, Xin", "He, Jia", "Wang, Hao"]
    assert records[0].year == 2026
    assert records[0].journal == "Journal of Ocean University of China"
    assert records[0].doi == "10.1007/s11802-026-6028-y"
    assert records[0].keywords == ["dual-anchor", "soft robot"]
    assert records[0].abstract.startswith("In this research")
    assert records[0].raw_bibtex.startswith("@ARTICLE")


def test_parse_pubmed_txt_reads_title_authors_and_abstract() -> None:
    records = parse_bibtex_files([Path(__file__).parent / "pubmed_sample.txt"], encoding="utf-8")

    assert len(records) == 5
    assert records[0].entry_type == "article"
    assert records[0].title == "Propolis in Obesity and Related Metabolic Disorders: Mechanistic and Clinical Insights-A Scoping Review."
    assert records[0].authors == ["Imre KE", "Akyol A"]
    assert records[0].year == 2026
    assert records[0].journal == "Nutrients"
    assert records[0].doi == "10.3390/nu18050826"
    assert records[0].abstract.startswith("OBJECTIVES: Obesity and related metabolic disorders")
    assert records[1].title.startswith("Compounds Contributing to the Modulation")
    assert records[1].doi == "10.3390/nu18050786"
    assert records[2].title == "Neomycin-sensitive gut bacteria-derived brassicasterol mediates the anti-obesity effects of Cordyceps militaris polysaccharide."
    assert records[2].journal == "Food Res Int"
    assert records[2].doi == "10.1016/j.foodres.2026.118574"
    assert records[2].authors == ["Cai J", "Huang A"]
    assert records[3].title == "Gpc3 selectively suppresses subcutaneous adipogenesis in diet-induced obesity."
    assert records[3].journal == "PLoS Biol"
    assert records[3].doi == "10.1371/journal.pbio.3003700"
    assert records[4].title == "Single-cell RNA sequencing uncovers molecular features underlying microglial lipid accumulation and depression-related behaviors in high-fat diet mouse model of obesity."
    assert records[4].authors == ["Liu C", "Li Z", "Ji JJ", "Liu K", "Samsom JN"]
    assert records[4].doi == "10.1038/s41386-025-02273-2"


def test_export_ris_writes_journal_type(tmp_path: Path) -> None:
    record = PaperRecord(
        paper_id="paper_000001",
        entry_type="article",
        title="Example Article",
        authors=["Alice Example", "Bob Example"],
        year=2026,
        journal="Journal of Testing",
        doi="10.1000/example",
        abstract="Abstract text.",
        keywords=["robot", "soil"],
    )

    output_path = tmp_path / "included.ris"
    export_ris([record], output_path)
    content = output_path.read_text(encoding="utf-8")

    assert "TY  - JOUR" in content
    assert "TI  - Example Article" in content
    assert "JO  - Journal of Testing" in content
    assert "DO  - 10.1000/example" in content


def test_build_screening_prompt_contains_ids_and_missing_markers() -> None:
    template_path = Path(__file__).resolve().parents[1] / "prompts" / "screening_prompt.md"
    criteria = CriteriaConfig(topic="test topic", inclusion=["keep relevant"], exclusion=["drop irrelevant"])
    papers = [
        PaperRecord(paper_id="paper_000001", title="Alpha", abstract="Summary text"),
        PaperRecord(paper_id="paper_000002", title="Beta", abstract=None, keywords=[]),
    ]

    prompt = build_screening_prompt(template_path=template_path, batch_id="batch_0001", criteria=criteria, papers=papers)

    assert "batch_0001" in prompt
    assert "paper_000001, paper_000002" in prompt
    assert "[ABSTRACT_MISSING]" in prompt
    assert "[KEYWORDS_MISSING]" in prompt
    assert '"batch_id"' in prompt


def test_validate_batch_response_accepts_exact_id_match() -> None:
    payload = {
        "batch_id": "batch_0001",
        "results": [
            {
                "paper_id": "paper_000001",
                "decision": "include",
                "reason": "matches",
                "evidence": ["title", "abstract"],
                "confidence": 0.9,
            },
            {
                "paper_id": "paper_000002",
                "decision": "exclude",
                "reason": "does not match",
                "evidence": ["abstract"],
                "confidence": 0.7,
            },
        ],
    }

    validate_batch_response(payload, expected_batch_id="batch_0001", expected_paper_ids=["paper_000001", "paper_000002"])


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {
                "batch_id": "batch_0001",
                "results": [
                    {
                        "paper_id": "paper_000001",
                        "decision": "include",
                        "reason": "matches",
                        "evidence": ["title"],
                        "confidence": 0.9,
                    }
                ],
            },
            "result count mismatch",
        ),
        (
            {
                "batch_id": "batch_other",
                "results": [
                    {
                        "paper_id": "paper_000001",
                        "decision": "include",
                        "reason": "matches",
                        "evidence": ["title"],
                        "confidence": 0.9,
                    },
                    {
                        "paper_id": "paper_000002",
                        "decision": "exclude",
                        "reason": "does not match",
                        "evidence": ["abstract"],
                        "confidence": 0.7,
                    },
                ],
            },
            "batch_id mismatch",
        ),
        (
            {
                "batch_id": "batch_0001",
                "results": [
                    {
                        "paper_id": "paper_000001",
                        "decision": "include",
                        "reason": "matches",
                        "evidence": ["title"],
                        "confidence": 0.9,
                    },
                    {
                        "paper_id": "paper_000001",
                        "decision": "exclude",
                        "reason": "duplicate",
                        "evidence": ["abstract"],
                        "confidence": 0.5,
                    },
                ],
            },
            "duplicate paper_id",
        ),
        (
            {
                "batch_id": "batch_0001",
                "results": [
                    {
                        "paper_id": "paper_000001",
                        "decision": "include",
                        "reason": "matches",
                        "evidence": ["title"],
                        "confidence": 0.9,
                    },
                    {
                        "paper_id": "paper_999999",
                        "decision": "exclude",
                        "reason": "unexpected",
                        "evidence": ["abstract"],
                        "confidence": 0.5,
                    },
                ],
            },
            "paper_id mismatch",
        ),
    ],
)
def test_validate_batch_response_rejects_bad_payloads(payload: dict, message: str) -> None:
    with pytest.raises(SchemaValidationError, match=message):
        validate_batch_response(payload, expected_batch_id="batch_0001", expected_paper_ids=["paper_000001", "paper_000002"])
