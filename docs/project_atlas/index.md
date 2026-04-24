# Project Atlas

`project_state.md` answers "what is true right now". This directory answers "where should I go when I need to change something".

## What This Layer Is For

- give new threads a spatial map of the repo instead of forcing them to reconstruct ownership from session history
- map feature requests to modules, files, and likely downstream impact
- keep `project_state.md` short while moving durable navigation knowledge into stable docs

## Reading Order For A New Thread

1. `project_state.md`
2. `docs/project_atlas/index.md`
3. `docs/project_atlas/change-routing.md`
4. the relevant `docs/project_atlas/modules/*.md` card
5. `project_session_log.md` or `docs/project_history/` only if older decisions still matter

## System Layers

| Layer | Owns | Main paths | Start here when... |
| --- | --- | --- | --- |
| Frontend views | thread pages, task pages, fulltext UI, report launch entry points | `literature_screening_web/src/views/` | the request is mostly page flow, wording, layout, or interaction |
| Frontend shell and stores | routing, API calls, polling, local draft persistence | `literature_screening_web/src/router/`, `literature_screening_web/src/stores/`, `literature_screening_web/src/api/` | route params, API field mapping, polling, or form persistence feel wrong |
| API and storage | HTTP boundary, schemas, task/project/dataset persistence | `literature_screening/src/literature_screening/api/`, `literature_screening/src/literature_screening/storage_paths.py` | payload shape, persistence, dataset lineage, or workbench state are wrong |
| Workflow orchestration | turns API payloads into runnable strategy/screening/report jobs | `literature_screening/src/literature_screening/studio/` | the UI payload is right but the actual run setup/output bridging is wrong |
| Screening pipeline | parse, dedupe, batch, prompt, validate, export screening outputs | `literature_screening/src/literature_screening/bibtex/`, `screening/`, `pipeline/` | imported records, batch behavior, LLM screening, or screening artifacts are wrong |
| Strategy generation | search-plan prompt building and rendering | `literature_screening/src/literature_screening/strategy/` | research-need extraction, database selection, or strategy markdown is wrong |
| Reporting | project report preparation and detached report generation | `literature_screening/src/literature_screening/reporting/`, `literature_screening/separated_modules/formal_report_module/` | report source selection, bibliography output, or report text generation is wrong |
| Runtime and operations | local startup, Docker topology, deployment, migration helpers | repo root scripts, `deploy/`, `scripts/` | the app will not start, migrate, or deploy cleanly |

## Cross-Module Flows

- Thread creation and editing:
  `ThreadNewView.vue` -> `stores/projects.ts` -> `api/app.py` -> `workspace_store.py`
- Strategy generation:
  `StrategyRunView.vue` -> `stores/tasks.ts` -> `api/app.py` -> `studio/service.py` -> `strategy/*`
- Screening run:
  `ScreeningRunView.vue` -> `stores/drafts.ts` and `stores/tasks.ts` -> `api/app.py` -> `studio/service.py` -> `bibtex/*`, `screening/*`, `pipeline/*`
- Screening detail and manual review:
  `TaskDetailView.vue` -> `components/ScreeningRecordsTable.vue` -> `stores/tasks.ts` -> `api/app.py` -> `workspace_store.py`
- Unified review and fulltext:
  `ProjectDetailView.vue` or `FulltextQueueView.vue` -> `stores/projects.ts` -> `api/app.py` -> `workspace_store.py`
- Report generation:
  `TaskDetailView.vue` or `ProjectDetailView.vue` -> `stores/tasks.ts` -> `api/app.py` -> `studio/service.py` -> `reporting/*` and detached report module

## Fast Heuristics

- If the problem is visible on a page, start with the view card before diving into stores or backend.
- If the payload shape, persisted metadata, or dataset lineage are wrong, start with the API/storage card.
- If the request body is right but the generated run directory, artifacts, or detached report inputs are wrong, start with orchestration.
- If the output files themselves are wrong, jump from orchestration into screening, strategy, or reporting.

## Module Cards

- [Backend API and Storage](./modules/backend-api-and-storage.md)
- [Workflow Orchestration](./modules/workflow-orchestration.md)
- [Screening and Data Pipeline](./modules/screening-and-data-pipeline.md)
- [Strategy Generation](./modules/strategy-generation.md)
- [Reporting and Formal Report Module](./modules/reporting-and-formal-report.md)
- [Frontend Shell and Stores](./modules/frontend-shell-and-stores.md)
- [Frontend Thread and Task Views](./modules/frontend-thread-and-task-views.md)
- [Runtime and Operations](./modules/runtime-and-operations.md)

## Maintenance Rules

- Update one module card whenever a feature meaningfully changes module ownership, entry points, or downstream dependencies.
- Update `change-routing.md` whenever a new class of recurring request appears.
- Keep `project_state.md` short; link to atlas docs instead of copying long ownership prose back into the state file.
- Use `project_session_log.md` for chronology and `docs/project_history/` for regression tracing, not for day-to-day navigation.
