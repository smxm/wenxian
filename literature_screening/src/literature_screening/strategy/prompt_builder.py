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
        You are designing a literature retrieval and screening plan.
        Return valid JSON only.

        The user has described a research need. You must:
        1. infer a clean research topic;
        2. draft practical inclusion and exclusion criteria for title/abstract screening;
        3. generate search strategies only for the selected databases;
        4. make the search blocks usable directly by a human researcher.

        Selected databases: {selected}

        Hard requirements:
        - Output keys must exactly match this schema:
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
        - For Scopus, Web of Science, and PubMed:
          - provide the advanced search expression in "query"
          - "lines" may be empty
        - For CNKI:
          - "query" must be null
          - "lines" must contain the advanced-search concept rows
          - each line must follow this style: "关键词 + 关键词 + 关键词"
          - here "+" means OR inside one row
          - these lines are meant for 知网高级检索的篇关摘 field
          - each row should represent one concept group and can later be combined manually in CNKI with AND between rows
        - Inclusion/exclusion must be concise, screening-oriented, and reusable by a later screening module.
        - Exclusion criteria must include major ambiguity/noise directions when they are obvious from the topic.
        - Keep the plan domain-specific. Do not output generic filler.

        Research need:
        {research_need.strip()}
        """
    ).strip()
