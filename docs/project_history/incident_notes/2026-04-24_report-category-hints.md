# 2026-04-24 Report Category Hint Contamination

## Symptom

Report tasks `a914285f8030` and `0a0365ee1ca1` were created with `deepseek-chat` and completed successfully, but their “类型划分” headings reused old domain labels such as “机器人控制与作业辅助”, “分子机制与信号通路”, and “冲击与贯入机制”.

## Finding

The raw overview files were valid JSON model responses, so this was not primarily a JSON parsing failure. The stale labels were already present in `report_output/paper_notes.json` as local `category` values, because `simple_report.py` had been deriving note `category_hint` from `build_fallback_literature_cards()`. The overview prompt then included those hints, so `deepseek-chat` followed polluted local input.

DeepSeek JSON mode remains compatible with the current request shape: the app sends `response_format: {"type": "json_object"}` and prompts contain JSON instructions. DeepSeek docs note that JSON mode still requires both `response_format` and JSON instructions in the prompt.

## Fix

- `simple_report.py` no longer imports `build_fallback_literature_cards()` for simple-report note hints.
- Simple-report note hints are now broad, domain-neutral labels.
- Overview prompts no longer include `category_hint`.
- Fallback grouping normalizes known stale categories to `主题相关研究`.
- API report-note cache seeding now targets the same `v2` cache generation used by the detached simple-report module.

## Verification

- `literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py` -> `9 passed`
- `literature_screening/tests/test_api_app.py -k 'report_task or report_source'` -> `4 passed, 24 deselected`
- Rebuilt overview prompts from the two affected tasks' existing `paper_notes.json`; the prompts contained no `category_hint` and none of the stale category labels.

## Follow-Up

Existing completed markdown artifacts will not update automatically. Rerun the report tasks after this fix to regenerate clean “类型划分” headings.
