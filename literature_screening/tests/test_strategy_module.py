from __future__ import annotations

from literature_screening.strategy.models import SearchStrategyBlock, SearchStrategyPlan
from literature_screening.strategy.prompt_builder import build_strategy_prompt
from literature_screening.strategy.renderer import render_strategy_markdown


def test_build_strategy_prompt_includes_cnki_constraints() -> None:
    prompt = build_strategy_prompt(
        research_need="研究 AI 与 XR 在猫咪情感识别中的应用",
        selected_databases=["scopus", "cnki"],
    )
    assert "关键词 + 关键词 + 关键词" in prompt
    assert "知网高级检索的篇关摘" in prompt
    assert "Scopus advanced search" in prompt
    assert '"topic" 必须是简体中文' in prompt
    assert 'Scopus、Web of Science、PubMed 的检索式必须使用英文专业检索表达' in prompt
    assert '"search_blocks" 中的 "title" 和 "notes" 必须使用简体中文' in prompt


def test_render_strategy_markdown_outputs_sections() -> None:
    plan = SearchStrategyPlan(
        topic="AI 与 XR 在猫咪交互中的应用",
        intent_summary="聚焦猫咪、伴侣动物与虚拟宠物的智能交互。",
        screening_topic="AI 与 XR 在猫咪与动物交互中的应用",
        inclusion=["涉及猫咪或伴侣动物", "包含 AI 或 XR 技术"],
        exclusion=["排除医学影像 PET 文献"],
        search_blocks=[
            SearchStrategyBlock(
                database="cnki",
                title="知网高级检索",
                query=None,
                lines=["猫咪 + 猫科动物 + 伴侣动物", "人工智能 + 机器学习 + 计算机视觉"],
                notes=["各行在知网高级检索中可分别填入篇关摘，再手动做 AND 组合。"],
            )
        ],
        caution_notes=["注意 PET 的歧义。"],
    )
    markdown = render_strategy_markdown(plan)
    assert "# 检索与筛选方案" in markdown
    assert "## 纳入标准" in markdown
    assert "### 知网高级检索" in markdown
    assert "猫咪 + 猫科动物 + 伴侣动物" in markdown
