from __future__ import annotations

from textwrap import dedent

from literature_screening.strategy.models import StrategyDatabase


DATABASE_LABELS: dict[StrategyDatabase, str] = {
    "scopus": "Scopus advanced search",
    "wos": "Web of Science advanced search",
    "pubmed": "PubMed advanced search",
    "cnki": "CNKI advanced search",
}


def build_strategy_prompt(*, research_need: str, selected_databases: list[StrategyDatabase]) -> str:
    selected = ", ".join(DATABASE_LABELS[item] for item in selected_databases)
    return dedent(
        f"""
        你正在为中文用户设计文献检索与初筛方案。
        只返回合法 JSON，不要输出额外解释。

        用户已经描述了研究需求。你必须：
        1. 提炼一个适合作为线程名展示的研究主题；
        2. 生成可直接复用的标题/摘要初筛纳入标准与排除标准；
        3. 只为用户选中的数据库生成检索方案；
        4. 让输出结果能被研究者直接拿去执行。

        已选数据库：{selected}

        输出键必须严格匹配下面这个 schema：
          {{
            "topic": string,
            "intent_summary": string,
            "screening_topic": string,
            "inclusion": [string, ...],
            "exclusion": [string, ...],
            "search_blocks": [
              {{
                "database": "scopus" | "wos" | "pubmed" | "cnki",
                "title": string,
                "query": string | null,
                "lines": [string, ...],
                "notes": [string, ...]
              }}
            ],
            "caution_notes": [string, ...]
          }}

        语言规则：
        - "topic" 必须是简体中文，长度适中，适合作为线程名称直接展示。
        - "intent_summary" 必须是简体中文，概括研究目标、对象或场景。
        - "screening_topic" 必须是简体中文，适合作为默认初筛主题。
        - "inclusion"、"exclusion"、"caution_notes" 必须全部使用简体中文。
        - "search_blocks" 中的 "title" 和 "notes" 必须使用简体中文。
        - Scopus、Web of Science、PubMed 的检索式必须使用英文专业检索表达，不要混入中文。
        - 如果 Scopus、Web of Science、PubMed 的 "lines" 不为空，也必须使用英文。
        - 知网检索块必须使用中文概念表达，不要混入英文句子。

        检索块规则：
        - 对于 Scopus、Web of Science、PubMed：
          - 在 "query" 中提供可直接使用的英文高级检索式
          - "lines" 可以为空
        - 对于知网：
          - "query" 必须为 null
          - "lines" 必须包含高级检索概念行
          - 每一行必须符合这种形式："关键词 + 关键词 + 关键词"
          - 这里的 "+" 表示同一行内 OR
          - 这些行用于知网高级检索的篇关摘字段
          - 每一行代表一个概念组，后续可在知网中按行与行之间手动做 AND

        质量要求：
        - 纳入/排除标准要简洁、适合初筛、可复用。
        - 排除标准在主题存在明显歧义或噪音方向时，必须主动覆盖这些方向。
        - 保持领域针对性，不要输出空泛套话。

        研究需求：
        {research_need.strip()}
        """
    ).strip()
