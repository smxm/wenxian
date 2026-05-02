# Reporting and Formal Report Module

## Owns

- report-task preparation from screening outputs or project datasets
- frontend/backend report source selection before task creation
- provider model discovery for report-generation model selection
- summary and writer logic in the main project
- detached formal-report generation and bibliography formatting

## Main Files

| File | Responsibility |
| --- | --- |
| `literature_screening/src/literature_screening/reporting/report_generator.py` | report generation entry logic inside the main project |
| `literature_screening/src/literature_screening/reporting/summary_builder.py` | assemble report summaries |
| `literature_screening/src/literature_screening/reporting/writers.py` | write report artifacts |
| `literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/simple_report.py` | simple-report note generation, overview grouping, fallback grouping, and markdown rendering |
| `literature_screening/separated_modules/formal_report_module/prompts/simple_report_overview_prompt.md` | overview/type-classification prompt for simple reports |
| `literature_screening/separated_modules/formal_report_module/` | detached report subsystem and scripts |
| `literature_screening_web/src/views/TaskDetailView.vue` | task-level report launch and report review surface |
| `literature_screening_web/src/views/ProjectDetailView.vue` | project-level report launch from chosen datasets, provider model dropdown, and source multi-select |

## Start Here When

- report launch inputs, source datasets, or report-source selection are wrong
- generated markdown, references, or detached report outputs are wrong
- model-specific report behavior needs tuning
- provider model lists fail to load or report model defaults fall back unexpectedly
- simple-report “类型划分” headings look copied from an unrelated old domain

## Typical Changes

- adjust how report tasks prepare screening-like inputs
- tune overview generation, paper-note handling, or bibliography output
- change report launch UI, source dataset options, or model options
- prevent local category hints or stale caches from leaking into the overview prompt

## Watch-Outs

- report tasks often depend on project-level `report_source` and `fulltext_ready` decisions, so inspect workbench code too
- reports can now target individual included/reviewed datasets, so do not assume report generation always uses all cumulative included records
- detached report behavior may look like a pure backend issue but still depend on orchestration defaults from `studio/service.py`
- bibliography metadata often comes from older pipeline artifacts, so parser/exporter changes can surface here
- `deepseek-chat` can return valid JSON while still following bad local input; inspect `report_output/paper_notes.json` and `report_output/raw/report_overview.txt` before assuming an API regression

## Common Verifications

- `PYTHONPATH=literature_screening/src python -m pytest literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py literature_screening/tests/test_api_app.py`
- browser report launch from both a screening task and the thread detail page
