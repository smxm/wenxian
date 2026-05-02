from __future__ import annotations

import json
from pathlib import Path

from literature_screening.core.models import ModelConfig
from literature_screening.screening.llm_client import ChatCompletionClient
from literature_screening.screening.response_parser import parse_model_json
from literature_screening.strategy.models import SearchStrategyPlan, StrategyDatabase
from literature_screening.strategy.prompt_builder import build_strategy_prompt
from literature_screening.strategy.renderer import render_strategy_markdown


def generate_search_strategy(
    *,
    research_need: str,
    selected_databases: list[StrategyDatabase],
    model_config: ModelConfig,
    timeout_seconds: int,
    output_dir: Path,
) -> SearchStrategyPlan:
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_strategy_prompt(research_need=research_need, selected_databases=selected_databases)
    client = ChatCompletionClient(model_config, timeout_seconds=timeout_seconds)
    raw_text = client.chat(prompt)
    (output_dir / "strategy_raw_response.txt").write_text(raw_text, encoding="utf-8")
    payload = parse_model_json(raw_text)
    plan = SearchStrategyPlan.model_validate(payload)
    (output_dir / "strategy_plan.json").write_text(
        json.dumps(plan.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "strategy_plan.md").write_text(render_strategy_markdown(plan), encoding="utf-8")
    return plan
