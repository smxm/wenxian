# Project Session Log

Append-only log for thread handoff. Add one new entry at the end of the file after each substantive session.

## Entry Template

### Session YYYY-MM-DD - short title

- Scope:
- Main changes:
- Verification:
- Outstanding follow-ups:
- Files touched:

## Session 2026-04-08 - Full-text workspace fixes and handoff structure

- Scope: fixed full-text queue source labeling and dataset-scoping bugs, then formalized the cross-thread handoff workflow
- Main changes:
  - corrected full-text round labels to use screening rounds sorted by creation time
  - added loading and error feedback for queue rebuild, OA/link refresh, and status-save actions
  - changed backend dataset validation to resolve derived datasets inside the current project instead of using global dataset-id lookup
  - added a regression test for project-scoped `cumulative-included`
  - rebuilt `E:\wenxian\project_state.md` into a strict summary template
  - created this append-only session log
- Verification:
  - `cd E:\wenxian\literature_screening_web && npm run typecheck`
  - `cd E:\wenxian\literature_screening_web && npm run build`
  - `cd E:\wenxian\literature_screening && python -m pytest literature_screening/tests/test_api_app.py -k "fulltext_queue_rebuild_and_status_update or project_scoped_cumulative_dataset"`
- Outstanding follow-ups:
  - keep checking for any remaining full-text page UX that still looks silent
  - decide later whether the session log needs a stronger checklist or can stay lightweight
- Files touched:
  - `E:\wenxian\literature_screening_web\src\views\FulltextQueueView.vue`
  - `E:\wenxian\literature_screening\src\literature_screening\api\app.py`
  - `E:\wenxian\literature_screening\tests\test_api_app.py`
  - `E:\wenxian\project_state.md`
  - `E:\wenxian\project_session_log.md`

## Session 2026-04-08 - Thread data migration helpers

- Scope: identified where persisted thread data lives and added helper scripts for exporting it to another machine
- Main changes:
  - confirmed thread and task state is stored under `E:\wenxian\literature_screening\data\api_runs`
  - added `E:\wenxian\scripts\export-api-runs.py` to export either the full `api_runs` tree or selected projects with related tasks
  - added `E:\wenxian\scripts\repair-api-runs-paths.py` to rewrite stored absolute paths after moving data from Windows to macOS
  - updated the handoff summary to mention the migration helpers
- Verification:
  - `cd E:\wenxian && python -m py_compile scripts\export-api-runs.py scripts\repair-api-runs-paths.py`
- Outstanding follow-ups:
  - add an optional import wrapper later if the Mac mini migration flow needs to be even more automated
  - if path portability becomes a recurring issue, move persisted metadata from absolute paths to repo-relative paths
- Files touched:
  - `E:\wenxian\scripts\export-api-runs.py`
  - `E:\wenxian\scripts\repair-api-runs-paths.py`
  - `E:\wenxian\project_state.md`
  - `E:\wenxian\project_session_log.md`

## Session 2026-04-09 - Mac local runtime and relative path persistence

- Scope: moved active development onto the Mac local Docker setup, imported Windows runtime data, and eliminated persisted absolute-path coupling by switching `api_runs` storage to relative paths
- Main changes:
  - synced the local repository to the latest GitHub `main` before continuing work
  - imported Windows `wenxian-api-runs` data into `/Users/mao/Documents/langchain/literature_screening/data/api_runs`
  - improved `/Users/mao/Documents/langchain/scripts/repair-api-runs-paths.py` during the migration work so JSON and YAML rewrites are safer
  - added local macOS start and stop helpers with `/Users/mao/Documents/langchain/start-wenxian.command`, `/Users/mao/Documents/langchain/stop-wenxian.command`, `/Users/mao/Documents/langchain/docker-compose.local.yml`, and `/Users/mao/Documents/langchain/literature_screening_web/deploy/nginx.local.conf`
  - updated `/Users/mao/Documents/langchain/literature_screening/Dockerfile` so the backend image builds reliably for local Docker use
  - diagnosed the full-text queue reset after report generation as a host-path versus container-path mismatch in persisted metadata
  - added `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/storage_paths.py` and routed task, dataset, and screening-config persistence through it so disk format is now relative to `api_runs`
  - added `/Users/mao/Documents/langchain/scripts/relativize-api-runs-paths.py` and migrated existing `api_runs` data to relative paths
  - added regression coverage for path dehydration and hydration in `/Users/mao/Documents/langchain/literature_screening/tests/test_task_store.py` and `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
  - created the reusable Codex handoff skill at `/Users/mao/.codex/skills/project-handoff-sync/SKILL.md`
- Verification:
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest literature_screening/tests/test_task_store.py literature_screening/tests/test_api_app.py`
  - `./.venv/bin/python -m compileall literature_screening/src/literature_screening/storage_paths.py literature_screening/src/literature_screening/api/task_store.py literature_screening/src/literature_screening/api/workspace_store.py literature_screening/src/literature_screening/core/config.py literature_screening/src/literature_screening/studio/service.py literature_screening/src/literature_screening/api/app.py scripts/relativize-api-runs-paths.py literature_screening/tests/test_task_store.py literature_screening/tests/test_api_app.py`
  - `./.venv/bin/python scripts/relativize-api-runs-paths.py --api-runs-root /Users/mao/Documents/langchain/literature_screening/data/api_runs`
  - `docker compose -f /Users/mao/Documents/langchain/docker-compose.local.yml up -d --build api`
  - `docker compose -f /Users/mao/Documents/langchain/docker-compose.local.yml ps`
  - `curl http://127.0.0.1:8000/api/health`
- Outstanding follow-ups:
  - decide later whether the API should expose stored-relative paths as well as resolved absolute paths
  - extend `storage_paths.py` if future persisted files introduce new path-like keys
  - consider whether the older Windows-path entries in this log should ever be backfilled, or should remain as historical context only
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/storage_paths.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/task_store.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/workspace_store.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/core/config.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/studio/service.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_task_store.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
  - `/Users/mao/Documents/langchain/scripts/repair-api-runs-paths.py`
  - `/Users/mao/Documents/langchain/scripts/relativize-api-runs-paths.py`
  - `/Users/mao/Documents/langchain/literature_screening/Dockerfile`
  - `/Users/mao/Documents/langchain/docker-compose.local.yml`
  - `/Users/mao/Documents/langchain/literature_screening_web/deploy/nginx.local.conf`
  - `/Users/mao/Documents/langchain/start-wenxian.command`
  - `/Users/mao/Documents/langchain/stop-wenxian.command`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`
  - `/Users/mao/.codex/skills/project-handoff-sync/SKILL.md`

## Session 2026-04-09 - API dual path compatibility fields

- Scope: evaluated whether the API should expose both absolute and stored-relative paths, then implemented the compatibility fields for dataset and task-detail responses
- Main changes:
  - added `relative_path` to dataset API responses while keeping the existing absolute `path`
  - added `run_root_relative` and `output_dir_relative` to task-detail responses while keeping the existing absolute fields
  - kept server-side runtime logic on hydrated absolute paths so review, report, and artifact flows do not need to change
  - updated frontend TypeScript response types to accept the new relative-path fields
  - added API regression tests covering both dataset and task-detail dual-path responses
- Verification:
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest /Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py -k 'relative_path or relative_task_paths or relative-path or dataset_api_returns_absolute_and_relative_paths or task_detail_api_returns_absolute_and_relative_task_paths or workspace_store_persists_dataset_paths_relatively or load_run_config_resolves_api_runs_relative_paths_from_storage_root'`
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest /Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
- Outstanding follow-ups:
  - decide when external callers and the web UI should start preferring the new relative-path fields over absolute-path assumptions
  - rerun frontend `typecheck` once a Node/npm toolchain is available on this machine
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/schemas.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/types/api.ts`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-09 - Documentation refresh for current workflow

- Scope: refreshed the public-facing docs so GitHub-facing usage notes match the current Docker-first local runtime and thread-first product shape
- Main changes:
  - rewrote the root `README.md` to describe the current startup flow, data layout, and path-compatibility behavior
  - updated `literature_screening/docs/architecture.md` to reflect strategy tasks, full-text workflow, `storage_paths.py`, and relative-path persistence
  - updated `literature_screening/docs/web-workbench.md` to reflect current routes, full-text page, Docker startup, and API surface
  - updated `literature_screening/separated_modules/formal_report_module/README.md` to document current simple/formal report entry points and module boundaries
- Verification:
  - `git diff --check README.md literature_screening/docs/architecture.md literature_screening/docs/web-workbench.md literature_screening/separated_modules/formal_report_module/README.md`
- Outstanding follow-ups:
  - if the Web UI starts consuming the new relative-path fields directly, update the web-workbench doc again to note that shift explicitly
  - the nested `literature_screening/README.md` still contains older environment notes and can be refreshed later if needed
- Files touched:
  - `/Users/mao/Documents/langchain/README.md`
  - `/Users/mao/Documents/langchain/literature_screening/docs/architecture.md`
  - `/Users/mao/Documents/langchain/literature_screening/docs/web-workbench.md`
  - `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/README.md`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-09 - Final handoff sync and Windows startup clarification

- Scope: finalized the branch handoff for the next thread and clarified that Windows uses the same local Docker compose flow even though the one-click scripts are macOS-only
- Main changes:
  - updated the root `README.md` to distinguish macOS `.command` launchers from Windows manual `docker compose -f docker-compose.local.yml up -d --build`
  - refreshed `project_state.md` to reflect the active branch `codex/relative-path-api-compat` and latest pushed commit `cc462c9`
  - noted that the remaining workspace noise is local untracked environment artifacts rather than tracked project changes
- Verification:
  - `git diff --check README.md`
  - `git status --short --branch`
- Outstanding follow-ups:
  - add Windows PowerShell start/stop wrappers later if manual Docker startup is too inconvenient
  - refresh `literature_screening/README.md` later so nested docs match the root README
- Files touched:
  - `/Users/mao/Documents/langchain/README.md`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-09 - Thread-first workflow redesign and persisted thread context

- Scope: reworked the main interaction flow so threads are created from a fuzzy research need, thread defaults persist on the backend, screening inherits thread context, and reporting is explicitly moved behind full-text acquisition
- Main changes:
  - added persisted `thread_profile` data to project metadata in `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/workspace_store.py` and exposed it through `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/schemas.py`
  - extended `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py` so strategy generation writes back thread-level research need, selected databases, generated plan, and default screening topic/criteria
  - added `/api/projects/{project_id}/workflow` for editing fixed thread context and `/api/tasks/{task_id}/review-overrides/selection` for direct multi-select review actions
  - turned `/Users/mao/Documents/langchain/literature_screening_web/src/views/StrategyRunView.vue` into the new `/threads/new` kickoff page focused on research need, provider/model, and database selection
  - redesigned `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue` around a fixed thread-context header plus four stages: thread plan, screening, full text, report
  - simplified `/Users/mao/Documents/langchain/literature_screening_web/src/views/ScreeningRunView.vue` so it emphasizes thread/source selection, file input, thread-default criteria, and minimal run settings
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/components/ScreeningRecordsTable.vue` and `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue` so screening review now supports multi-select actions plus year filter and year sorting
  - removed direct report creation from screening task detail and made the thread/report UI depend on `fulltext_ready` data instead
- Verification:
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest literature_screening/tests/test_api_app.py -q`
  - `./.venv/bin/python -m compileall literature_screening/src/literature_screening/api/app.py literature_screening/src/literature_screening/api/schemas.py literature_screening/src/literature_screening/api/workspace_store.py literature_screening/tests/test_api_app.py`
  - `docker run --rm -v /Users/mao/Documents/langchain/literature_screening_web:/work -w /work node:20 sh -lc 'npm ci >/tmp/npm-ci.log && npm run build >/tmp/npm-build.log && cat /tmp/npm-build.log'`
  - `git diff --check literature_screening/src/literature_screening/api/app.py literature_screening/src/literature_screening/api/schemas.py literature_screening/src/literature_screening/api/workspace_store.py literature_screening/tests/test_api_app.py literature_screening_web/src/api/client.ts literature_screening_web/src/components/ScreeningRecordsTable.vue literature_screening_web/src/layouts/AppShell.vue literature_screening_web/src/router/index.ts literature_screening_web/src/stores/drafts.ts literature_screening_web/src/stores/projects.ts literature_screening_web/src/stores/tasks.ts literature_screening_web/src/types/api.ts literature_screening_web/src/utils/strategy.ts literature_screening_web/src/views/DashboardView.vue literature_screening_web/src/views/ProjectDetailView.vue literature_screening_web/src/views/ScreeningRunView.vue literature_screening_web/src/views/StrategyRunView.vue literature_screening_web/src/views/TaskDetailView.vue`
- Outstanding follow-ups:
  - consider whether to write a one-off migration that materializes derived `thread_profile` data into all older project JSON files
  - investigate frontend bundle-size warnings later if production chunking starts to matter
  - refresh `/Users/mao/Documents/langchain/literature_screening/README.md` so nested docs match the new thread-first flow
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/schemas.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/workspace_store.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/api/client.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/components/ScreeningRecordsTable.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/layouts/AppShell.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/router/index.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/stores/drafts.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/stores/projects.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/stores/tasks.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/types/api.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/utils/strategy.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/DashboardView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ScreeningRunView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/StrategyRunView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-09 - Hot-reload local development mode

- Scope: removed the need to rebuild the whole local stack for routine UI and API edits by adding a separate Dockerized development mode with source mounts and automatic reload
- Main changes:
  - added `/Users/mao/Documents/langchain/docker-compose.dev.yml` with bind-mounted backend source plus `uvicorn --reload`
  - added `/Users/mao/Documents/langchain/start-wenxian-dev.command` and `/Users/mao/Documents/langchain/stop-wenxian-dev.command` for one-click dev startup on macOS
  - updated `/Users/mao/Documents/langchain/literature_screening_web/vite.config.ts` so Dockerized Vite can use env-configured API proxy, polling watch mode, and HMR client port
  - updated `/Users/mao/Documents/langchain/start-wenxian.command` and `/Users/mao/Documents/langchain/stop-wenxian.command` to separate stable mode from dev mode and avoid port-conflict confusion
  - refreshed `/Users/mao/Documents/langchain/README.md` and handoff notes so the two runtime modes are documented for the next thread
- Verification:
  - `docker compose -p literature-screening-dev -f /Users/mao/Documents/langchain/docker-compose.dev.yml up -d`
  - `curl http://127.0.0.1:8000/api/health`
  - `curl http://127.0.0.1:8080`
  - `docker compose -p literature-screening-dev -f /Users/mao/Documents/langchain/docker-compose.dev.yml logs --tail=80 web`
  - `git diff --check README.md docker-compose.dev.yml start-wenxian.command stop-wenxian.command start-wenxian-dev.command stop-wenxian-dev.command literature_screening_web/vite.config.ts project_state.md project_session_log.md`
- Outstanding follow-ups:
  - if local Node is installed later, decide whether to keep Dockerized Vite as the default dev path or move hot-update work back to host tooling
  - if Windows convenience becomes important, add matching PowerShell wrappers for the new dev runtime
- Files touched:
  - `/Users/mao/Documents/langchain/docker-compose.dev.yml`
  - `/Users/mao/Documents/langchain/start-wenxian.command`
  - `/Users/mao/Documents/langchain/stop-wenxian.command`
  - `/Users/mao/Documents/langchain/start-wenxian-dev.command`
  - `/Users/mao/Documents/langchain/stop-wenxian-dev.command`
  - `/Users/mao/Documents/langchain/literature_screening_web/vite.config.ts`
  - `/Users/mao/Documents/langchain/README.md`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-09 - Thread-scoped plan and screening entry cleanup

- Scope: removed duplicate thread selection from thread-internal plan/screening flows and added clearer return-to-thread navigation from child pages
- Main changes:
  - added thread-scoped frontend routes for plan refresh and screening kickoff under `/threads/:projectId/plan/new` and `/threads/:projectId/screening/new`
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue` so thread actions always launch thread-internal plan and screening pages instead of the generic global entry
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/StrategyRunView.vue` so refreshing a plan from inside a thread no longer shows an extra thread selector and instead presents the current thread as fixed context
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/ScreeningRunView.vue` so thread-internal screening no longer allows implicit new-thread creation, shows the current thread context, and provides direct return-to-thread buttons
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue`, `/Users/mao/Documents/langchain/literature_screening_web/src/layouts/AppShell.vue`, and `/Users/mao/Documents/langchain/literature_screening_web/src/views/DashboardView.vue` so drafts and task pages route back into the owning thread instead of bouncing users through a global picker
- Verification:
  - `docker compose -p literature-screening-dev -f /Users/mao/Documents/langchain/docker-compose.dev.yml exec -T web npm run build`
  - `git diff --check literature_screening_web/src/router/index.ts literature_screening_web/src/views/ProjectDetailView.vue literature_screening_web/src/views/TaskDetailView.vue literature_screening_web/src/views/StrategyRunView.vue literature_screening_web/src/views/ScreeningRunView.vue literature_screening_web/src/layouts/AppShell.vue literature_screening_web/src/views/DashboardView.vue`
- Outstanding follow-ups:
  - decide later whether the generic `/screening/new` route should stay as a lightweight global picker or be replaced by a dedicated thread chooser page
  - consider adding the same explicit “返回线程主页” affordance to any future standalone report-edit pages if report interactions move back out of the thread homepage
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening_web/src/router/index.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/StrategyRunView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ScreeningRunView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/layouts/AppShell.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/DashboardView.vue`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-09 - Confidence-first review order and merged full-text review stage

- Scope: made screening review prioritize relevance, then folded more of the final manual curation into the full-text workspace instead of keeping it conceptually separate
- Main changes:
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/components/ScreeningRecordsTable.vue` so screening records default to confidence-first ordering and keep confidence as the tie-breaker inside each year bucket
  - extended `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/schemas.py`, `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/workspace_store.py`, and `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py` so full-text queue items now carry screening confidence/reason context and support a dedicated `excluded` status
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue` to act as “全文获取与最终复核工作台”, including relevance-aware sorting, displayed screening rationale, and a direct “复审排除” action
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue` and `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue` so the main workflow now points users toward the merged full-text/final-review stage, while keeping task-detail review tools as advanced optional fixes
  - updated `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/core/models.py`, `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/bibtex/parser.py`, `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/bibtex/deduper.py`, and `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/bibtex/exporter.py` so imported URL fields are preserved end-to-end and can be reused as landing links when DOI is missing
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/layouts/AppShell.vue` and `/Users/mao/Documents/langchain/literature_screening_web/src/views/DashboardView.vue` so the global copy consistently frames the flow as initial screening -> full-text review -> report
  - added regression coverage in `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py` for confidence propagation into the full-text queue, the new `excluded` status, and imported-URL fallback when DOI is absent
- Verification:
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest /Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py -q`
  - `docker compose -p literature-screening-dev -f /Users/mao/Documents/langchain/docker-compose.dev.yml exec -T web npm run build`
  - `git diff --check literature_screening/src/literature_screening/api/schemas.py literature_screening/src/literature_screening/api/workspace_store.py literature_screening/src/literature_screening/api/app.py literature_screening/src/literature_screening/core/models.py literature_screening/src/literature_screening/bibtex/parser.py literature_screening/src/literature_screening/bibtex/deduper.py literature_screening/src/literature_screening/bibtex/exporter.py literature_screening/tests/test_api_app.py literature_screening_web/src/types/api.ts literature_screening_web/src/api/client.ts literature_screening_web/src/stores/projects.ts literature_screening_web/src/components/ScreeningRecordsTable.vue literature_screening_web/src/views/FulltextQueueView.vue literature_screening_web/src/views/ProjectDetailView.vue literature_screening_web/src/views/TaskDetailView.vue literature_screening_web/src/layouts/AppShell.vue literature_screening_web/src/views/DashboardView.vue`
- Outstanding follow-ups:
  - evaluate later whether uncertain papers should also be promoted into the merged full-text/final-review workspace instead of staying only in the screening detail layer
  - if imported RIS/EndNote metadata lacks a usable URL, discuss later whether title-based CNKI/Wanfang/VIP search is worth the complexity; for now, do not auto-scrape those sources
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/schemas.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/workspace_store.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/core/models.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/bibtex/parser.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/bibtex/deduper.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/bibtex/exporter.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/types/api.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/api/client.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/stores/projects.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/components/ScreeningRecordsTable.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/layouts/AppShell.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/DashboardView.vue`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-09 - Full-text review batching and include-only boundary cleanup

- Scope: made the merged full-text/final-review workspace feel closer to the original review flow by restoring bulk actions, switching its default order to year-first, and tightening the boundary so excluded/uncertain screening outcomes do not conceptually bleed into full-text work
- Main changes:
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue` so the full-text page now defaults to year-desc ordering with relevance as the secondary sort inside each year, shows explicit selection checkboxes, and restores batch actions such as bulk exclude, bulk ready, bulk defer, and bulk unavailable
  - added `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/schemas.py`, `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`, `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/workspace_store.py`, `/Users/mao/Documents/langchain/literature_screening_web/src/api/client.ts`, and `/Users/mao/Documents/langchain/literature_screening_web/src/stores/projects.ts` support for batch full-text status updates so the UI can update many selected papers with one rebuild instead of spamming single-item requests
  - tightened screening-context enrichment in `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py` so full-text queue context now matches by DOI / normalized title instead of unstable per-run `paper_id`, and later screening decisions of `exclude` / `uncertain` now remove matching items from the full-text queue instead of letting them linger there
  - added regression coverage in `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py` for batch full-text status updates, for preventing excluded context from another screening round from leaking into the full-text queue via `paper_id` collision, and for filtering out papers whose latest matched screening decision is no longer `include`
- Verification:
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest /Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py -q`
  - `docker compose -p literature-screening-dev -f /Users/mao/Documents/langchain/docker-compose.dev.yml exec -T web npm run build`
  - `git diff --check literature_screening/src/literature_screening/api/app.py literature_screening/src/literature_screening/api/schemas.py literature_screening/src/literature_screening/api/workspace_store.py literature_screening/tests/test_api_app.py literature_screening_web/src/api/client.ts literature_screening_web/src/stores/projects.ts literature_screening_web/src/views/FulltextQueueView.vue`
- Outstanding follow-ups:
  - if future users want “不确定” records to enter a dedicated secondary queue, add that as an explicit optional source class instead of silently mixing it into the full-text queue
  - consider later whether the full-text page should visually group cards by year headers now that year-first sorting is the default
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/schemas.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/workspace_store.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/api/client.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/stores/projects.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-09 - Dashboard refresh and sidebar thread context menu

- Scope: cleaned up the homepage hierarchy so it reads more clearly, and made the sidebar recent-thread list support direct context actions instead of forcing users to hunt for edit/delete entry points
- Main changes:
  - redesigned `/Users/mao/Documents/langchain/literature_screening_web/src/views/DashboardView.vue` into a more balanced hero + overview + recent-thread layout, replacing the old sparse “如何使用” area with denser workflow guidance and reducing visual clutter on thread cards
  - changed recent thread cards on the dashboard to use a compact action dropdown instead of always showing separate edit/delete icon buttons
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/layouts/AppShell.vue` so sidebar recent-thread items are sorted by update time, highlight the active thread, and support right-click context actions for open, edit, and delete
  - added a lightweight global thread edit modal in `/Users/mao/Documents/langchain/literature_screening_web/src/layouts/AppShell.vue` so sidebar context-menu editing no longer requires bouncing through the homepage first
- Verification:
  - `docker compose -p literature-screening-dev -f /Users/mao/Documents/langchain/docker-compose.dev.yml exec -T web npm run build`
  - `git diff --check literature_screening_web/src/layouts/AppShell.vue literature_screening_web/src/views/DashboardView.vue`
- Outstanding follow-ups:
  - consider later whether the sidebar recent-thread list should also expose the same context menu on touch devices via a small visible “more” affordance
  - consider later whether the homepage recent-thread grid should support right-click context actions too, for parity with the sidebar
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening_web/src/layouts/AppShell.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/DashboardView.vue`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-09 - Unified screening and full-text review workspace

- Scope: merged the duplicated-feeling screening review and full-text acquisition interactions into a single review workspace while preserving each side's core controls
- Main changes:
  - rewrote `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue` into a unified “筛选与全文复核工作台” with two tabs on one route: `筛选复核` and `全文获取`
  - kept the screening-side powers inside the new screening tab, including selected-round review, single-record decision edits, multi-select batch review overrides, and title/reference-list matching
  - kept the full-text-side powers inside the full-text tab, including year-first queue ordering, OA/link refresh, selection-based batch status updates, per-item full-text notes, and final curation states
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue` so the screening task page now opens the unified workspace directly on the screening-review tab for the current screening round
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue` so the thread homepage now consistently labels stage 3 as a unified review workspace instead of presenting screening follow-up and full-text acquisition as separate destinations
- Verification:
  - `docker compose -p literature-screening-dev -f /Users/mao/Documents/langchain/docker-compose.dev.yml exec -T web npm run build`
  - `git diff --check literature_screening_web/src/layouts/AppShell.vue literature_screening_web/src/views/DashboardView.vue literature_screening_web/src/views/FulltextQueueView.vue literature_screening_web/src/views/ProjectDetailView.vue literature_screening_web/src/views/TaskDetailView.vue`
- Outstanding follow-ups:
  - split `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue` into smaller subcomponents once the merged interaction settles down
  - consider adding a visible touch-friendly “more” button for sidebar thread actions so edit/delete remain discoverable without right click
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/layouts/AppShell.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/DashboardView.vue`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-09 - Unified candidate stream redesign for review workspace

- Scope: refined the first merged review workspace so it no longer feels like two pages glued together, and removed the duplicated screening-record table from the screening task detail page
- Main changes:
  - rewrote `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue` again so the review area is now one continuous candidate stream with a right-side action panel instead of `筛选复核` / `全文获取` tabs
  - removed the old default-first-record behavior from the review workspace, so entering the page no longer auto-selects a paper before the user clicks or checks one
  - updated the unified candidate rows to show screening decision, confidence, and full-text stage together, while the right-side panel now switches between single-record handling, batch handling, and title/reference-list batch matching
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue` so screening task detail now focuses on round summary, thread criteria, outputs, and next actions instead of repeating the review table and advanced-fix forms
  - simplified the screening-task jump into the review workspace so it now only passes `screeningTaskId` instead of a tab-specific route intent
- Verification:
  - `docker compose -p literature-screening-dev -f /Users/mao/Documents/langchain/docker-compose.dev.yml exec -T web npm run build`
  - `git diff --check literature_screening_web/src/views/FulltextQueueView.vue literature_screening_web/src/views/TaskDetailView.vue project_state.md project_session_log.md`
- Outstanding follow-ups:
  - split `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue` into smaller subcomponents once the new candidate-stream interaction settles down
  - consider later whether the unified candidate stream should add optional year headers once larger real-world projects make the year-first order feel dense
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-10 - Strategy localization and thread auto-rename

- Scope: fixed the new-thread kickoff flow so generated strategy output becomes the thread’s visible identity, and localized strategy output by database so the resulting topic, summary, criteria, and search syntax match the expected Chinese/English split
- Main changes:
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/StrategyRunView.vue` and `/Users/mao/Documents/langchain/literature_screening_web/src/stores/drafts.ts` so opening “新建线程” no longer auto-fills the last saved draft; the page now stays blank and only restores old content when the user explicitly chooses to do so
  - updated `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/strategy/prompt_builder.py` so `topic`, `intent_summary`, `screening_topic`, inclusion/exclusion criteria, notes, and CNKI rows are required in Chinese, while Scopus / WoS / PubMed search expressions are required in English
  - updated `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py` so a completed strategy task now renames the thread to the generated `topic`, updates the thread description to the generated Chinese `intent_summary`, and keeps the generated Chinese `screening_topic` as the screening default
  - added regression coverage in `/Users/mao/Documents/langchain/literature_screening/tests/test_strategy_module.py` and `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py` for the new language contract and for post-strategy thread rename / description persistence
- Verification:
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest /Users/mao/Documents/langchain/literature_screening/tests/test_strategy_module.py /Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py -q`
  - `git diff --check /Users/mao/Documents/langchain/literature_screening/src/literature_screening/strategy/prompt_builder.py /Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py /Users/mao/Documents/langchain/literature_screening/tests/test_strategy_module.py /Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
- Outstanding follow-ups:
  - older threads that already generated a strategy before this update still need one manual “重新生成线程方案” run if the user wants their visible name, summary, and criteria refreshed into the new localized format
  - if later users want database titles themselves localized differently by provider, refine the renderer and thread summary cards without changing the core prompt contract again
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/StrategyRunView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/stores/drafts.ts`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/strategy/prompt_builder.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_strategy_module.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-11 - Rename active branch to thread-first workflow refresh

- Scope: renamed the long-lived working branch so its name matches the current product scope instead of the older relative-path-only backend fix
- Main changes:
  - renamed the local git branch from `codex/relative-path-api-compat` to `codex/thread-first-workflow-refresh`
  - pushed the renamed branch to GitHub and removed the old remote branch name to keep the remote clean
  - updated `/Users/mao/Documents/langchain/project_state.md` so current-branch and remote-tracking references now point at the renamed branch
- Verification:
  - `git branch --show-current`
  - `git push -u origin codex/thread-first-workflow-refresh`
  - `git push origin --delete codex/relative-path-api-compat`
- Outstanding follow-ups:
  - if a later PR is opened from this work, use `codex/thread-first-workflow-refresh` as the head branch name
- Files touched:
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`

## Session 2026-04-15 - Windows startup, legacy data compatibility, and handoff sync

- Scope: stabilized the Windows local runtime, fixed old/new project data compatibility issues in the unified review flow, refreshed repo docs, and corrected the handoff records to match the actual `E:\wenxian_new` workspace
- Main changes:
  - added Windows start/stop helpers for both dev and build flows in `E:\wenxian_new\start-wenxian-dev.ps1`, `E:\wenxian_new\start-wenxian.ps1`, `E:\wenxian_new\stop-wenxian-dev.ps1`, and `E:\wenxian_new\stop-wenxian.ps1` with matching `.cmd` wrappers
  - made Docker readiness checks more robust and added automatic port probing so the dev launcher can survive harmless `docker info` warnings and common `8080` conflicts
  - fixed old-data path resolution in `E:\wenxian_new\literature_screening\src\literature_screening\storage_paths.py` so persisted `.../api_runs/...` Windows absolute paths from older workspaces are remapped into the current repo storage root
  - fixed `cumulative_included` and full-text queue rebuild behavior in `E:\wenxian_new\literature_screening\src\literature_screening\api\workspace_store.py` so queue regeneration preserves original `paper_id` values and imported landing-page links by preferring task outputs over RIS-only reconstruction
  - added related compatibility support in `E:\wenxian_new\literature_screening\src\literature_screening\bibtex\parser.py`, `E:\wenxian_new\literature_screening\src\literature_screening\bibtex\exporter.py`, `E:\wenxian_new\literature_screening\src\literature_screening\bibtex\deduper.py`, and `E:\wenxian_new\literature_screening\src\literature_screening\studio\service.py`
  - updated `E:\wenxian_new\README.md` and `E:\wenxian_new\literature_screening\docs\architecture.md` to document Windows startup, `.env` precedence, API-key troubleshooting, old-data compatibility, and report fallback behavior
  - pushed the implementation branch to `origin/codex/thread-first-workflow-refresh` at commit `d9c5230`
  - refreshed `E:\wenxian_new\project_state.md` so future threads read the actual Windows workspace state instead of stale macOS handoff notes
- Verification:
  - `cd E:\wenxian_new\literature_screening && cmd /c "set PYTHONPATH=E:\wenxian_new\literature_screening\src&& python -m pytest -q tests\test_storage_paths.py"`
  - `cd E:\wenxian_new\literature_screening && cmd /c "set PYTHONPATH=E:\wenxian_new\literature_screening\src&& python -m pytest -q tests\test_api_app.py -k fulltext_queue"`
  - `cd E:\wenxian_new && git push -u origin codex/thread-first-workflow-refresh`
- Outstanding follow-ups:
  - decide whether daily Windows development should continue on Docker or move to direct host execution for speed
  - consider reducing configuration confusion by making only one `.env` file authoritative
  - if report output still lacks substance with a valid API key, inspect report prompt quality and fallback-note behavior separately from data-queue logic
- Files touched:
  - `E:\wenxian_new\README.md`
  - `E:\wenxian_new\literature_screening\docs\architecture.md`
  - `E:\wenxian_new\literature_screening\src\literature_screening\api\app.py`
  - `E:\wenxian_new\literature_screening\src\literature_screening\api\workspace_store.py`
  - `E:\wenxian_new\literature_screening\src\literature_screening\bibtex\deduper.py`
  - `E:\wenxian_new\literature_screening\src\literature_screening\bibtex\exporter.py`
  - `E:\wenxian_new\literature_screening\src\literature_screening\bibtex\parser.py`
  - `E:\wenxian_new\literature_screening\src\literature_screening\storage_paths.py`
  - `E:\wenxian_new\literature_screening\src\literature_screening\studio\service.py`
  - `E:\wenxian_new\literature_screening\tests\test_api_app.py`
  - `E:\wenxian_new\literature_screening\tests\test_storage_paths.py`
  - `E:\wenxian_new\start-wenxian-dev.ps1`
  - `E:\wenxian_new\start-wenxian.ps1`
  - `E:\wenxian_new\stop-wenxian-dev.ps1`
  - `E:\wenxian_new\stop-wenxian.ps1`
  - `E:\wenxian_new\project_state.md`
  - `E:\wenxian_new\project_session_log.md`

## Session 2026-04-16 - Workbench stabilization, thread-first flow cleanup, report polish, and handoff refresh

- Scope: fixed the newly reworked candidate workbench so status actions and migrated states behave correctly again, simplified the thread-first creation/detail flow, refined report-stage behavior, and refreshed the handoff docs for the current macOS workspace
- Main changes:
  - fixed the candidate workbench action path end to end by updating `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue`, `/Users/mao/Documents/langchain/literature_screening_web/src/stores/projects.ts`, and `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py` so single-item and batch status changes no longer fail on an undefined store action or a misrouted backend `batch` path
  - added legacy workbench reconciliation in `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/workspace_store.py` so old `fulltext_queue.json` and `fulltext_statuses.json` restore acquired/full-report decisions and preserved links into the new project-level workbench
  - simplified new-thread behavior so `/threads/new` creates the thread from the research need first, while later thread-page actions handle manual criteria editing, AI-assisted extraction, or full search-strategy generation; added backend helper coverage for `POST /api/threads/prefill`
  - reworked `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue` and `/Users/mao/Documents/langchain/literature_screening_web/src/components/ThreadMessageCard.vue` so the thread header keeps only the edit entry, the lower action row owns the four stage buttons, duplicate stage-card buttons are removed, and the report stage stays visible even when included records are `0`
  - added report model-selection inputs on the thread page and fixed formal-report GB/T 7714 page extraction by reading structured `volume` / `number` / `pages` fields in `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/core/models.py` and `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/reference_list.py`
  - shortened verbose explanatory copy across the current production frontend so the main workflow pages emphasize the next action instead of long guidance text
- Verification:
  - `git -C /Users/mao/Documents/langchain diff --check`
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src /Users/mao/Documents/langchain/literature_screening/.venv311-codex/bin/python -m pytest -q /Users/mao/Documents/langchain/literature_screening/tests /Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py`
  - result: `51 passed`
- Outstanding follow-ups:
  - run frontend build/typecheck on a machine with `node` / `npm` / `pnpm`
  - browser-test real threads with migrated data to verify the new workbench reconciliation and report model-selection flows
  - split `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue` and `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue` into smaller components now that the page direction is clearer
  - decide later whether `POST /api/threads/prefill` should stay as an internal helper or come back as a visible post-creation assist action
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/workspace_store.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/schemas.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/core/models.py`
  - `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/reference_list.py`
  - `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/components/ThreadMessageCard.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/stores/projects.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/DashboardView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ScreeningRunView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/StrategyRunView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ThreadNewView.vue`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`
  - `/Users/mao/Documents/langchain/docs/project_history/index.md`

## Session 2026-04-18 - Project atlas navigation layer

- Scope: redesigned the handoff docs so new threads can navigate by module ownership and change-entry points instead of relying on chronology alone
- Main changes:
  - created `/Users/mao/Documents/langchain/docs/project_atlas/index.md` as a repo navigation layer that separates current state, history, and module ownership
  - added `/Users/mao/Documents/langchain/docs/project_atlas/change-routing.md` to map common change requests to the first files and downstream modules that usually matter
  - added `/Users/mao/Documents/langchain/docs/project_atlas/invariants.md` plus module cards for backend API/storage, orchestration, screening pipeline, strategy, reporting, frontend shell/stores, frontend views, and runtime/ops
  - updated `/Users/mao/Documents/langchain/README.md` and `/Users/mao/Documents/langchain/project_state.md` so the next thread is directed into the atlas first
  - archived the previous state file into `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-18_1430_project_state.md` and appended the redesign to the history index
- Verification:
  - `git -C /Users/mao/Documents/langchain diff --check -- README.md project_state.md project_session_log.md docs/project_history/index.md docs/project_atlas/index.md docs/project_atlas/change-routing.md docs/project_atlas/invariants.md docs/project_atlas/modules/backend-api-and-storage.md docs/project_atlas/modules/workflow-orchestration.md docs/project_atlas/modules/screening-and-data-pipeline.md docs/project_atlas/modules/strategy-generation.md docs/project_atlas/modules/reporting-and-formal-report.md docs/project_atlas/modules/frontend-shell-and-stores.md docs/project_atlas/modules/frontend-thread-and-task-views.md docs/project_atlas/modules/runtime-and-operations.md`
  - `find /Users/mao/Documents/langchain/docs/project_atlas -maxdepth 2 -type f | sort`
  - `rg -n "Reading Order|Change Routing|Invariants|Module Cards" /Users/mao/Documents/langchain/docs/project_atlas/index.md /Users/mao/Documents/langchain/docs/project_atlas/change-routing.md /Users/mao/Documents/langchain/docs/project_atlas/invariants.md`
  - `node -v`
  - `npm -v`
  - result: atlas files are in place and `diff --check` should stay clean; `node` is present locally, but frontend typecheck is still blocked on missing local `npm`
- Outstanding follow-ups:
  - decide whether to update the shared `/Users/mao/.codex/skills/update-project-state/SKILL.md` so atlas maintenance becomes part of the reusable skill itself
  - keep the relevant module card and change-routing row updated whenever a new feature changes ownership boundaries
  - use the atlas to support the next pass of splitting the largest Vue views into smaller components
- Files touched:
  - `/Users/mao/Documents/langchain/README.md`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`
  - `/Users/mao/Documents/langchain/docs/project_history/index.md`
  - `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-18_1430_project_state.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/index.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/change-routing.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/invariants.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/backend-api-and-storage.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/workflow-orchestration.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/screening-and-data-pipeline.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/strategy-generation.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/reporting-and-formal-report.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/frontend-shell-and-stores.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/frontend-thread-and-task-views.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/runtime-and-operations.md`

## Session 2026-04-16 - Report-generation diagnosis, reasoner hardening, and bibliography metadata repair

- Scope: traced the current simple-report generation path for `asks`/task `cd13976ef17e`, compared `deepseek-reasoner` and `deepseek-chat` behavior on the same project, fixed the actual GB/T 7714 page-loss chain, and hardened the fallback/report-token behavior for humanities-style report runs
- Main changes:
  - confirmed from `/Users/mao/Documents/langchain/literature_screening/data/api_runs/tasks/cd13976ef17e/report_output/raw/report_overview.txt` and `/Users/mao/Documents/langchain/literature_screening/data/api_runs/tasks/cd13976ef17e/report_output/logs/report_overview_errors.log` that the `deepseek-reasoner` report did not produce overview JSON at all, so the backend fell back instead of using model-generated categories
  - verified that the report path itself is not chat-only: `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/simple_report.py` calls the same `ChatCompletionClient` for both `deepseek-chat` and `deepseek-reasoner`, but the frontend had still been hardcoding `max_tokens: 1536` for report submission while DeepSeek’s reasoning model counts CoT and final answer together
  - updated `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`, `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/screening/llm_client.py`, and `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue` so report tasks normalize `deepseek-reasoner` to at least `4096` tokens and emit a clearer error when reasoning content is returned without final answer text
  - fixed the real bibliography bug by populating `PaperRecord.volume` / `number` / `pages` in `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/bibtex/parser.py`, preserving them in `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/bibtex/deduper.py`, and exporting them from `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/bibtex/exporter.py` with a `raw_bibtex` fallback so old stored records can be repaired too
  - refined `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/fallback.py` and `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/simple_report.py` so report fallback for Chinese humanities topics no longer defaults to a single “相关机制研究” bucket, and bumped the shared note-cache version to avoid reusing the old bad classification cache
  - rebuilt `/Users/mao/Documents/langchain/literature_screening/data/api_runs/projects/6e2959b2aa63/derived/report_source.ris` after the exporter repair and confirmed that the current project’s report source now carries `VL` / `IS` / `SP` / `EP` lines again
- Verification:
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src /Users/mao/Documents/langchain/literature_screening/.venv311-codex/bin/python -m pytest -q /Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py /Users/mao/Documents/langchain/literature_screening/tests/test_screening_pipeline.py /Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py`
  - result: `50 passed`
  - `git -C /Users/mao/Documents/langchain diff --check -- literature_screening/src/literature_screening/bibtex/exporter.py literature_screening/src/literature_screening/bibtex/parser.py literature_screening/src/literature_screening/bibtex/deduper.py literature_screening/src/literature_screening/screening/llm_client.py literature_screening/src/literature_screening/api/app.py literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/simple_report.py literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/fallback.py literature_screening_web/src/views/ProjectDetailView.vue literature_screening/tests/test_screening_pipeline.py literature_screening/tests/test_api_app.py literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py`
  - rebuilt current project workbench/report-source dataset locally and confirmed `/Users/mao/Documents/langchain/literature_screening/data/api_runs/projects/6e2959b2aa63/derived/report_source.ris` contains page-related RIS tags again
- Outstanding follow-ups:
  - rerun the repaired report flow with a valid `DEEPSEEK_API_KEY`, because this shell currently reports `DEEPSEEK_API_KEY` as missing and therefore could not perform a live model-backed report regeneration
  - validate in the real UI that a fresh `deepseek-reasoner` report on project `6e2959b2aa63` now keeps multiple humanities categories and auto-generated GB/T 7714 page ranges without requiring manual reference override
  - consider exposing model-specific token guidance in the report UI so reasoning models are not silently sent with chat-oriented token budgets again
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/bibtex/deduper.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/bibtex/exporter.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/bibtex/parser.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/screening/llm_client.py`
  - `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/fallback.py`
  - `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/simple_report.py`
  - `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_screening_pipeline.py`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`
  - `/Users/mao/Documents/langchain/docs/project_history/index.md`

## Session 2026-04-16 - Tencent Cloud update-path review and handoff refresh

- Scope: refreshed the reusable handoff with the current deployment guidance, then read the Tencent Cloud deployment docs and scripts to extract the exact server update flow for this repo
- Main changes:
  - verified that `/Users/mao/Documents/langchain/project_state.md` already captured the report-generation fixes from the previous session, then refreshed it so future threads can immediately find the Tencent Cloud deployment docs alongside the recent report fixes
  - cross-checked `/Users/mao/Documents/langchain/deploy/cloud-server.md`, `/Users/mao/Documents/langchain/deploy/server-update.sh`, `/Users/mao/Documents/langchain/deploy/migrate-persistent-storage.sh`, and `/Users/mao/Documents/langchain/docker-compose.yml`; the intended update path is still “local tarball -> upload to `/opt` -> run `deploy/server-update.sh`”, with runtime data mounted from `/opt/wenxian-data/api_runs` and Basic Auth read from `/opt/wenxian-secrets/.htpasswd`
  - noted one documentation caveat for follow-up: the repo root currently does not contain `.env.deploy.example`, so a first deployment may need a manually created `/opt/wenxian/.env` even though the markdown examples reference copying a template
- Verification:
  - `sed -n '1,260p' /Users/mao/Documents/langchain/deploy/cloud-server.md`
  - `sed -n '1,260p' /Users/mao/Documents/langchain/deploy/server-update.sh`
  - `sed -n '1,220p' /Users/mao/Documents/langchain/deploy/migrate-persistent-storage.sh`
  - `sed -n '1,220p' /Users/mao/Documents/langchain/docker-compose.yml`
  - `sed -n '1,220p' /Users/mao/Documents/langchain/README.md`
- Outstanding follow-ups:
  - add back a checked-in deploy-env template or update the Tencent Cloud doc to state clearly that `/opt/wenxian/.env` may need to be written by hand on first deploy
  - perform one live cloud update rehearsal after the next packaged release so the documented server path is validated end to end on the actual Tencent Cloud instance
- Files touched:
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`
  - `/Users/mao/Documents/langchain/docs/project_history/index.md`

## Session 2026-04-18 - Screening naming, detail-summary cleanup, and handoff refresh

- Scope: caught up on the current thread-first workflow state, then refined the screening UI so new rounds can be named explicitly and screening detail pages better expose source context
- Main changes:
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/ScreeningRunView.vue` to add an optional “初筛名称” input when creating a screening round; leaving it blank still falls back to the existing auto-generated `${thread}-round-${n}` pattern
  - preserved the new custom-name field through draft persistence and submission so reruns and “返回编辑” flows can keep the chosen screening title instead of forcing a regenerated default
  - updated `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue` so “本轮筛选摘要” now shows uploaded file names from `request_payload.uploaded_file_names`, and the source text better reflects mixed lineage when a round combines prior datasets with fresh uploads
  - removed the redundant “本轮产出与后续动作” block from the screening detail page because the next-step handoff to unified review is already shown elsewhere on the page
  - archived the previous `/Users/mao/Documents/langchain/project_state.md` snapshot and refreshed the handoff docs for the current macOS workspace
- Verification:
  - `git -C /Users/mao/Documents/langchain diff --check -- literature_screening_web/src/views/ScreeningRunView.vue literature_screening_web/src/views/TaskDetailView.vue`
  - `rg -n "buildTaskTitle|continueUnusedRoute" /Users/mao/Documents/langchain/literature_screening_web/src/views/ScreeningRunView.vue /Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue`
  - `node -v`
  - `npm -v`
  - `cd /Users/mao/Documents/langchain/literature_screening_web && npm run typecheck`
  - result: `diff --check` clean, the stale helper references are gone, but `node` / `npm` are not installed on this machine so frontend typecheck could not run locally
- Outstanding follow-ups:
  - browser-test the new custom screening-name flow and confirm the chosen title reads well on the thread page and task detail page
  - decide whether historical screening tasks need a metadata backfill if uploaded file names should appear consistently in old detail pages too
  - run frontend build/typecheck on a machine with `node` / `npm`
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ScreeningRunView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`
  - `/Users/mao/Documents/langchain/docs/project_history/index.md`
  - `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-18_1045_project_state.md`

## Session 2026-04-24 - Screening/fulltext workbench refresh and simple-report taxonomy fix

- Scope: refreshed the reusable docs for the latest screening and fulltext-workbench changes, then investigated why two `deepseek-chat` simple reports reused old type-classification templates.
- Main changes:
  - documented the recent screening controls: target included-paper stop, manual stop with partial-output preservation, per-round criteria snapshots, screening task deletion, and task/thread edit affordances.
  - documented the fulltext workbench redesign: full-width candidate overview, left-side Scopus/WoS-style filters, 10-record pagination, relevance/year sorting, temporary screening-round selection, range/page/all multi-select, and inline single-paper actions.
  - inspected report tasks `a914285f8030` and `0a0365ee1ca1`; both had valid `deepseek-chat` JSON in `report_output/raw/report_overview.txt`, but their `paper_notes.json` categories already contained stale local fallback labels such as “机器人控制与作业辅助”, “分子机制与信号通路”, and “冲击与贯入机制”.
  - fixed `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/simple_report.py` so simple-report note generation uses neutral category hints instead of `build_fallback_literature_cards`, overview prompts no longer include `category_hint`, fallback grouping normalizes stale cached categories, and API-side report note-cache seeding now targets the same `v2` cache generation.
  - tightened `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/prompts/simple_report_overview_prompt.md` so overview categories must be supported by the current notes and must not reuse unrelated historical domain names.
  - archived the previous `/Users/mao/Documents/langchain/project_state.md` snapshot and updated `project_state.md`, the history index, and relevant atlas module cards/routing notes.
- Verification:
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src /Users/mao/Documents/langchain/literature_screening/.venv311-codex/bin/python -m pytest -q literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py`
  - result: `9 passed`
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src /Users/mao/Documents/langchain/literature_screening/.venv311-codex/bin/python -m pytest -q literature_screening/tests/test_api_app.py -k 'report_task or report_source'`
  - result: `4 passed, 24 deselected`
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src /Users/mao/Documents/langchain/literature_screening/.venv311-codex/bin/python -m py_compile literature_screening/src/literature_screening/api/app.py literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/simple_report.py literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py`
  - checked regenerated overview prompts for `a914285f8030` and `0a0365ee1ca1`; neither includes `category_hint` nor the stale old-category terms.
  - `git -C /Users/mao/Documents/langchain diff --check -- literature_screening/src/literature_screening/api/app.py literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/simple_report.py literature_screening/separated_modules/formal_report_module/prompts/simple_report_overview_prompt.md literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py`
- Outstanding follow-ups:
  - rerun the two affected report tasks or create fresh report tasks to regenerate markdown with clean type headings; existing completed report artifacts will not rewrite themselves.
  - browser-test the new fulltext workbench states, especially long round names, one selected record, multiple selected records, and temporary rounds.
  - separately review DeepSeek model defaults if the live account stops accepting `deepseek-chat`; the observed stale categories were local prompt contamination, not a JSON-output parse failure.
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`
  - `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/src/literature_screening/formal_report/simple_report.py`
  - `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/prompts/simple_report_overview_prompt.md`
  - `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`
  - `/Users/mao/Documents/langchain/docs/project_history/index.md`
  - `/Users/mao/Documents/langchain/docs/project_history/incident_notes/2026-04-24_report-category-hints.md`
  - `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-24_report-and-workbench_state.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/change-routing.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/frontend-thread-and-task-views.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/frontend-shell-and-stores.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/backend-api-and-storage.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/workflow-orchestration.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/reporting-and-formal-report.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/screening-and-data-pipeline.md`

## Session 2026-04-24 - Pre-push verification and handoff refresh

- Scope: refreshed the current handoff with the latest verification results, archived the pre-push project state, and prepared the current feature branch for GitHub publishing.
- Main changes:
  - archived `/Users/mao/Documents/langchain/project_state.md` into `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-24_1841_project_state.md` before updating the live state snapshot.
  - updated `/Users/mao/Documents/langchain/project_state.md` so future threads see the direct Vue typecheck command that works on this machine despite `npm` being unavailable.
  - kept local runtime artifacts out of the intended publish scope, including `.venv/`, `literature_screening/data/`, `build/`, and `.DS_Store` files.
- Verification:
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src /Users/mao/Documents/langchain/literature_screening/.venv311-codex/bin/python -m pytest -q literature_screening/tests/test_api_app.py literature_screening/tests/test_task_store.py literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py`
  - result: `40 passed`
  - `cd /Users/mao/Documents/langchain/literature_screening_web && /Applications/Codex.app/Contents/Resources/node node_modules/vue-tsc/bin/vue-tsc.js --noEmit`
  - result: passed
  - `git -C /Users/mao/Documents/langchain diff --check`
- Outstanding follow-ups:
  - perform a real browser walkthrough after pulling the pushed branch elsewhere, especially the fulltext workbench and screening stop/delete flows.
  - rerun affected report tasks to regenerate clean type headings in existing completed reports.
- Files touched:
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`
  - `/Users/mao/Documents/langchain/docs/project_history/index.md`
  - `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-24_1841_project_state.md`

## Session 2026-04-24 - Report source selection, provider model discovery, and live screening progress

- Scope: updated the report-generation entry point so model names and report sources are user-selectable without manual model typing, corrected the screening-task edit affordance, and made screening counts update during long-running jobs.
- Main changes:
  - added `/api/model-options` in `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`, with schemas in `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/schemas.py`, to load provider model lists from OpenAI-compatible `/models` endpoints using the entered API key or server env var.
  - changed `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue` so the report model name is a refreshable dropdown and the report source is a multi-select over report-source, fulltext-ready, cumulative included, and individual included/reviewed screening datasets.
  - changed `/Users/mao/Documents/langchain/literature_screening_web/src/views/ScreeningRunView.vue` so new initial-screening tasks use the same provider model dropdown instead of a free-text model-name input.
  - changed `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue` so screening task detail shows “编辑初筛任务” instead of the mistaken thread-edit button; it restores the saved task payload into the screening form for a corrected new submission.
  - updated `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/pipeline/run_pipeline.py` and the API screening progress callback so task summaries pick up `run_summary.json` after each completed batch, exposing live processed/included/excluded/uncertain counts.
  - archived the previous current-state file into `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-24_1902_project_state.md` and refreshed the project state plus atlas routing/module notes.
- Verification:
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src /Users/mao/Documents/langchain/literature_screening/.venv311-codex/bin/python -m pytest -q literature_screening/tests/test_api_app.py -k 'meta_endpoint or model_options or screening_progress_callback or report_task or report_source'`
  - result: `8 passed, 23 deselected`
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src /Users/mao/Documents/langchain/literature_screening/.venv311-codex/bin/python -m pytest -q literature_screening/tests/test_api_app.py literature_screening/tests/test_task_store.py literature_screening/tests/test_screening_pipeline.py literature_screening/separated_modules/formal_report_module/tests/test_simple_report.py`
  - result: `58 passed`
  - `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src /Users/mao/Documents/langchain/literature_screening/.venv311-codex/bin/python -m py_compile literature_screening/src/literature_screening/api/app.py literature_screening/src/literature_screening/api/schemas.py literature_screening/src/literature_screening/pipeline/run_pipeline.py`
  - `cd /Users/mao/Documents/langchain/literature_screening_web && /Applications/Codex.app/Contents/Resources/node node_modules/vue-tsc/bin/vue-tsc.js --noEmit`
  - `git -C /Users/mao/Documents/langchain diff --check`
  - attempted Vite startup with bundled Codex Node, but local `node_modules` is missing `@rollup/rollup-darwin-arm64`; browser walkthrough was not run.
- Outstanding follow-ups:
  - browser-test the new report-source selector, report/screening model dropdown fallback/provider-load states, and screening edit handoff after frontend dependencies are repaired.
  - run one real multi-batch screening task to visually confirm live counts on both the thread card and task detail page.
  - consider extending provider model dropdowns to the strategy form if the report/screening version feels right.
- Files touched:
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/schemas.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/pipeline/run_pipeline.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/api/client.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/types/api.ts`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ScreeningRunView.vue`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue`
  - `/Users/mao/Documents/langchain/project_state.md`
  - `/Users/mao/Documents/langchain/project_session_log.md`
  - `/Users/mao/Documents/langchain/docs/project_history/index.md`
  - `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-24_1902_project_state.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/change-routing.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/backend-api-and-storage.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/frontend-shell-and-stores.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/frontend-thread-and-task-views.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/reporting-and-formal-report.md`
  - `/Users/mao/Documents/langchain/docs/project_atlas/modules/screening-and-data-pipeline.md`

## Session 2026-04-24 - Documentation path hygiene, legacy archive, and doc-router skill

- Scope: cleaned the active project handoff/docs so future threads use workspace-relative paths, archived stale architecture/workbench notes, and created a skill for fast doc-driven edit routing.
- Main changes:
  - archived the previous `project_state.md` into `docs/project_history/state_snapshots/2026-04-24_2359_project_state.md`.
  - normalized current handoff, history-index, README, deploy, atlas, and skill docs toward repo-relative paths; older snapshots and earlier session-log entries remain unchanged as historical records.
  - moved `literature_screening/docs/architecture.md` and `literature_screening/docs/web-workbench.md` into `docs/archive/legacy-docs/literature_screening/`, with `docs/archive/legacy-docs/README.md` explaining that atlas docs are now the current source of truth.
  - refreshed `README.md`, `literature_screening/README.md`, `literature_screening_web/README.md`, and `deploy/cloud-server.md` to remove stale local Windows/macOS workspace assumptions from active instructions.
  - added `$project-doc-router` at `$CODEX_HOME/skills/project-doc-router/SKILL.md` and mirrored it into `skills/project-doc-router/SKILL.md`; it reads `project_state.md`, `docs/project_atlas/`, and relevant module cards before naming likely edit files and verification.
  - updated `$update-project-state` in Codex home and `skills/update-project-state/SKILL.md` so active docs prefer workspace-relative paths and immutable historical snapshots are not rewritten for cosmetic path cleanup.
- Verification:
  - path-hygiene `rg` scans over active docs, README files, deploy docs, and `skills/`; no project absolute-path or old drive-letter matches remained
  - `find docs/archive/legacy-docs "$CODEX_HOME/skills/project-doc-router" skills/project-doc-router -maxdepth 3 -type f -print` confirmed the archive and skill files
  - `git diff --check` passed
- Outstanding follow-ups:
  - try `$project-doc-router` in the next feature thread and adjust its output expectations if it routes too broadly.
  - keep historical snapshots immutable; add new rows/entries instead of back-editing older logs when path conventions change.
- Files touched:
  - `project_state.md`
  - `project_session_log.md`
  - `docs/project_history/index.md`
  - `docs/project_history/state_snapshots/2026-04-24_2359_project_state.md`
  - `docs/project_atlas/index.md`
  - `docs/project_atlas/change-routing.md`
  - `docs/project_atlas/invariants.md`
  - `docs/project_atlas/modules/documentation-handoff-and-skills.md`
  - `docs/project_atlas/modules/backend-api-and-storage.md`
  - `docs/project_atlas/modules/frontend-shell-and-stores.md`
  - `docs/project_atlas/modules/frontend-thread-and-task-views.md`
  - `docs/project_atlas/modules/reporting-and-formal-report.md`
  - `docs/project_atlas/modules/runtime-and-operations.md`
  - `docs/project_atlas/modules/screening-and-data-pipeline.md`
  - `docs/project_atlas/modules/workflow-orchestration.md`
  - `docs/archive/legacy-docs/README.md`
  - `docs/archive/legacy-docs/literature_screening/architecture.md`
  - `docs/archive/legacy-docs/literature_screening/web-workbench.md`
  - `README.md`
  - `deploy/cloud-server.md`
  - `literature_screening/README.md`
  - `literature_screening_web/README.md`
  - `skills/update-project-state/SKILL.md`
  - `skills/project-doc-router/SKILL.md`
  - `$CODEX_HOME/skills/update-project-state/SKILL.md`
  - `$CODEX_HOME/skills/project-doc-router/SKILL.md`

## Session 2026-05-02 - Provider model discovery and screening enhancements

- Scope: added provider model discovery endpoint, enhanced screening configuration parameters, refactored fulltext queue view, and updated project documentation.
- Main changes:
  - added `/api/model-options` endpoint for fetching model lists from provider APIs (DeepSeek, Kimi) with fallback defaults.
  - added new screening configuration parameters: `batch_size`, `target_include_count`, `stop_when_target_reached`, `min_include_confidence`, `allow_uncertain`, `retry_times`, `request_timeout_seconds`, `encoding`.
  - refactored `FulltextQueueView.vue` with improved filtering, pagination, multi-select, and enrichment workflows.
  - updated `ProjectDetailView.vue`, `ScreeningRunView.vue`, `TaskDetailView.vue` with UI improvements.
  - added comprehensive tests for API endpoints (`test_api_app.py`) and screening pipeline (`test_screening_pipeline.py`).
  - updated project atlas and module cards to reflect new features.
- Verification:
  - backend tests passed
  - frontend vue-tsc passed
  - git diff --check passed
- Outstanding follow-ups:
  - browser-test provider model discovery with different API key configurations
  - test fulltext queue refactoring with real data
  - verify screening configuration changes end-to-end
- Files touched:
  - `project_state.md`
  - `project_session_log.md`
  - `literature_screening/src/literature_screening/api/app.py`
  - `literature_screening/src/literature_screening/api/schemas.py`
  - `literature_screening/src/literature_screening/pipeline/run_pipeline.py`
  - `literature_screening/src/literature_screening/screening/llm_client.py`
  - `literature_screening/src/literature_screening/screening/prompt_builder.py`
  - `literature_screening/src/literature_screening/studio/service.py`
  - `literature_screening/tests/test_api_app.py`
  - `literature_screening/tests/test_screening_pipeline.py`
  - `literature_screening_web/src/views/FulltextQueueView.vue`
  - `literature_screening_web/src/views/ProjectDetailView.vue`
  - `literature_screening_web/src/views/ScreeningRunView.vue`
  - `literature_screening_web/src/views/TaskDetailView.vue`
  - `docs/project_atlas/change-routing.md`
  - `docs/project_atlas/index.md`
  - `docs/project_atlas/invariants.md`
  - `docs/project_atlas/modules/backend-api-and-storage.md`
  - `docs/project_atlas/modules/frontend-shell-and-stores.md`
  - `docs/project_atlas/modules/frontend-thread-and-task-views.md`
  - `docs/project_atlas/modules/reporting-and-formal-report.md`
  - `docs/project_atlas/modules/screening-and-data-pipeline.md`
  - `docs/project_history/index.md`
