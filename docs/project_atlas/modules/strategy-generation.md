# Strategy Generation

## Owns

- research-need to search-plan prompt building
- database-specific strategy rendering
- structured plan models reused between thread state and strategy task output

## Main Files

| File | Responsibility |
| --- | --- |
| `literature_screening/src/literature_screening/strategy/generator.py` | generate structured strategy output |
| `literature_screening/src/literature_screening/strategy/prompt_builder.py` | compose LLM prompts for strategy work |
| `literature_screening/src/literature_screening/strategy/renderer.py` | render markdown and presentation-friendly output |
| `literature_screening/src/literature_screening/strategy/models.py` | structured models for strategy payloads |
| `literature_screening_web/src/views/StrategyRunView.vue` | primary UI entry for strategy creation or refresh |

## Start Here When

- research need extraction, selected databases, or strategy markdown are wrong
- thread-level strategy defaults or latest-plan reuse feel off
- you need to change how the strategy stage feeds later screening criteria

## Typical Changes

- adjust prompt wording or database-specific output shape
- expand structured plan models
- change how the UI preloads thread context into the strategy form

## Watch-Outs

- strategy output feeds `thread_profile`, so API/storage changes may be needed if the plan structure changes
- if the screening stage auto-seeds topic or criteria from strategy results, inspect both `api/app.py` and `ProjectDetailView.vue` or `StrategyRunView.vue`

## Common Verifications

- browser strategy generation from `/threads/:projectId/plan/new`
- `literature_screening/tests/test_api_app.py` if payload or persistence changed
