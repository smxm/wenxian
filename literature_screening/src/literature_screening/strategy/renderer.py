from __future__ import annotations

from literature_screening.strategy.models import SearchStrategyPlan


def render_strategy_markdown(plan: SearchStrategyPlan) -> str:
    lines: list[str] = [
        "# 检索与筛选方案",
        "",
        "## 研究主题",
        "",
        plan.topic,
        "",
        "## 需求概括",
        "",
        plan.intent_summary,
        "",
        "## 建议用于初筛的研究主题",
        "",
        plan.screening_topic,
        "",
        "## 纳入标准",
        "",
    ]
    lines.extend(f"- {item}" for item in plan.inclusion)
    lines.extend(["", "## 排除标准", ""])
    lines.extend(f"- {item}" for item in plan.exclusion)
    lines.extend(["", "## 检索词与高级检索式", ""])

    for block in plan.search_blocks:
        lines.extend([f"### {block.title}", ""])
        if block.query:
            lines.extend(["```text", block.query.strip(), "```", ""])
        if block.lines:
            lines.extend(f"- {row}" for row in block.lines)
            lines.append("")
        if block.notes:
            lines.extend(f"- 说明：{note}" for note in block.notes)
            lines.append("")

    if plan.caution_notes:
        lines.extend(["## 检索边界与注意事项", ""])
        lines.extend(f"- {item}" for item in plan.caution_notes)
        lines.append("")

    return "\n".join(lines).strip() + "\n"
