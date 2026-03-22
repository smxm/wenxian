from __future__ import annotations

from pathlib import Path

from literature_screening.formal_report.models import LiteratureCard
from literature_screening.formal_report.models import ReportOverviewPayload
from literature_screening.formal_report.text_utils import normalize_text


def render_formal_report_markdown(
    overview: ReportOverviewPayload,
    cards: list[LiteratureCard],
    output_path: Path,
) -> None:
    card_map = {card.paper_id: card for card in cards}
    high_priority_cards = _select_recommended_cards(cards)
    ordered_cards = _order_cards_by_category(cards, overview)

    lines = [f"# {overview.report_title}", ""]
    lines.extend(["## 一、文献总体概览", "", overview.overview.strip(), "", "---", ""])

    lines.extend(["## 二、分类整理与分析", ""])
    for index, category in enumerate(overview.category_overviews, start=1):
        lines.append(f"### 2.{index} {category.category_name}")
        lines.append("")
        lines.append(category.category_summary.strip())
        lines.append("")
        lines.append(f"这一方向对本主题的主要参考价值在于：{category.category_value.strip()}")
        if category.representative_paper_ids:
            lines.append("")
            lines.append("相关代表文献包括：")
            for paper_id in category.representative_paper_ids:
                card = card_map.get(paper_id)
                if card is not None:
                    lines.append(f"- {_original_title(card)}")
        lines.append("")

    lines.extend(["---", "", "## 三、建议优先阅读的文献", ""])
    for index, card in enumerate(high_priority_cards, start=1):
        lines.append(f"### {index}. {_original_title(card)}")
        lines.append("")
        lines.append(card.content_summary.one_sentence_summary.strip())
        lines.append("")
        lines.append(f"优先阅读理由：{card.content_summary.value_for_topic.strip()}")
        lines.append("")

    lines.extend(["---", "", "## 四、纳入文献逐篇整理", ""])
    for index, card in enumerate(ordered_cards, start=1):
        lines.append(f"### {index}. {_original_title(card)}")
        lines.append("")
        translated_title = _translated_title(card)
        if translated_title:
            lines.append(f"中文题目：{translated_title}  ")
        lines.append(f"作者：{_format_authors(card.source_record.authors)}  ")
        lines.append(f"年份：{card.source_record.year if card.source_record.year is not None else '未注明'}  ")
        lines.append(f"来源：{normalize_text(card.source_record.journal) or '未注明'}  ")
        lines.append(f"DOI：{card.source_record.doi or '未注明'}")
        lines.append("")
        lines.append("文献概述：")
        lines.append(card.content_summary.core_summary.strip())
        lines.append("")
        lines.append(f"研究重点可概括为：{card.content_summary.research_focus.strip()}")
        lines.append("")
        lines.append("就本次主题而言，这篇文献的参考价值主要体现在：")
        lines.append(card.content_summary.value_for_topic.strip())
        lines.append("")
        lines.append("从现有题目与摘要信息来看，这篇文献仍有以下方面需要后续阅读时进一步确认：")
        lines.append(card.content_summary.limitations.strip())
        lines.append("")

    lines.extend(["---", "", "## 五、简要结论", "", overview.conclusion.strip(), "", "---", ""])
    lines.extend(["## 附录：文献信息一览", ""])
    lines.extend(["| 序号 | 标题 | 作者 | 年份 | 来源 | DOI |", "| --- | --- | --- | --- | --- | --- |"])
    for index, card in enumerate(ordered_cards, start=1):
        lines.append(
            f"| {index} | {_original_title(card)} | {_format_authors(card.source_record.authors)} | "
            f"{card.source_record.year if card.source_record.year is not None else ''} | "
            f"{normalize_text(card.source_record.journal) or ''} | {card.source_record.doi or ''} |"
        )
    lines.append("")
    lines.append("如需导入文献管理软件，可同时附上对应的 BibTeX 或其他标准格式文献文件。")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def _select_recommended_cards(cards: list[LiteratureCard]) -> list[LiteratureCard]:
    key_cards = [card for card in cards if card.reporting_flags.is_key_paper]
    if key_cards:
        return sorted(key_cards, key=_recommended_sort_key)[:5]
    return sorted(cards, key=_recommended_sort_key)[:5]


def _recommended_sort_key(card: LiteratureCard) -> tuple[int, int]:
    level_order = {"high": 0, "medium": 1, "low": 2}
    return (
        level_order.get(card.reporting_flags.recommended_level, 3),
        -(card.source_record.year or 0),
    )


def _order_cards_by_category(cards: list[LiteratureCard], overview: ReportOverviewPayload) -> list[LiteratureCard]:
    category_order = {item.category_name: index for index, item in enumerate(overview.category_overviews)}
    return sorted(
        cards,
        key=lambda card: (
            category_order.get(card.classification.primary_category, 999),
            _recommended_sort_key(card),
            _original_title(card),
        ),
    )


def _original_title(card: LiteratureCard) -> str:
    return (normalize_text(card.source_record.title_en) or "").strip() or (normalize_text(card.source_record.title_zh) or "").strip()


def _translated_title(card: LiteratureCard) -> str | None:
    title_zh = (normalize_text(card.source_record.title_zh) or "").strip()
    original_title = _original_title(card)
    if not title_zh or title_zh == original_title:
        return None
    return title_zh


def _format_authors(authors: list[str]) -> str:
    cleaned = [normalize_text(author) for author in authors if normalize_text(author)]
    return "；".join(cleaned) if cleaned else "未注明"
