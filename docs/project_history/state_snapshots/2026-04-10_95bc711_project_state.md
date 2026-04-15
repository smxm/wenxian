# Project State

Last updated: 2026-04-10

## Project Overview

- Workspace root: `/Users/mao/Documents/langchain`
- Git branch: `codex/relative-path-api-compat`
- Remote tracking branch: `origin/codex/relative-path-api-compat`
- Backend: `/Users/mao/Documents/langchain/literature_screening`
- Frontend: `/Users/mao/Documents/langchain/literature_screening_web`
- Report module: `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module`
- Local runtime: Docker-based on macOS, with API on `http://127.0.0.1:8000` and web UI on `http://127.0.0.1:8080`; stable mode uses `docker-compose.local.yml`, and a new hot-reload dev mode uses `docker-compose.dev.yml`
- Product direction: thread-first literature workflow, with the thread object as the main user-facing concept and project/task/dataset kept mostly hidden in the UI
- Current imported workspace snapshot: `54` projects are visible through the local API

## Current Product Shape

Main stages:

1. Create or refresh a thread from a fuzzy research need, then generate topic, screening criteria, and database search syntax
2. Start screening rounds that inherit the thread's fixed topic and criteria by default
3. Review screening results inside a unified review workspace with one candidate stream: click a paper for single-record handling, or multi-select for batch review and batch full-text actions
4. In that same unified review workspace, move included studies through full-text acquisition states such as `pending` / `ready` / `unavailable` / `deferred`
5. Generate reports only after full-text-ready records are available

Core capabilities already in place:

- Screening pipeline supports merge, dedupe, batching, manual review override, and continue-from-unused
- Supported import formats include `.bib`, `.ris`, `.enw`, and text exports such as PubMed-style txt
- Strategy generation supports Scopus, WoS, PubMed, and CNKI query output
- Strategy generation now targets a localized mixed-language output contract: thread name, topic summary, inclusion/exclusion criteria, and CNKI guidance are Chinese, while Scopus / WoS / PubMed advanced queries stay English
- Unified review workspace now exposes one continuous candidate list plus a context-sensitive right-side action panel; screening correction and full-text handling happen against the same selected records instead of two separate subpages
- Reports are now explicitly positioned after full-text acquisition in the main UI flow, while the backend still supports `GB/T 7714` and `APA7`
- Persisted task and dataset metadata now stores `api_runs`-relative paths on disk and resolves them back to absolute paths at runtime

## This Round Changes

Date: 2026-04-10

- Pulled the latest GitHub changes to the local `main` branch without overwriting unrelated local edits
- Imported Windows `wenxian-api-runs` data into `/Users/mao/Documents/langchain/literature_screening/data/api_runs`
- Improved `/Users/mao/Documents/langchain/scripts/repair-api-runs-paths.py` earlier in this round so JSON and YAML path rewrites are safer during cross-machine import
- Added a macOS local-start flow with:
  - `/Users/mao/Documents/langchain/start-wenxian.command`
  - `/Users/mao/Documents/langchain/stop-wenxian.command`
  - `/Users/mao/Documents/langchain/docker-compose.local.yml`
  - `/Users/mao/Documents/langchain/literature_screening_web/deploy/nginx.local.conf`
  - `/Users/mao/Documents/langchain/literature_screening/Dockerfile`
- Diagnosed the “full-text data disappears after generating report” bug as a persisted absolute-path mismatch between host paths like `/Users/mao/...` and container paths like `/app/...`
- Added a shared storage-path layer at `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/storage_paths.py`
- Rewired persisted path handling through:
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/task_store.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/workspace_store.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/core/config.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/studio/service.py`
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`
- Added `/Users/mao/Documents/langchain/scripts/relativize-api-runs-paths.py` to migrate existing `api_runs` content from absolute paths to repo-relative storage
- Migrated the current `api_runs` data to relative paths; `551` files were rewritten
- Rebuilt the API container and verified that persisted data no longer contains `/app/`, `/Users/mao/Documents/langchain/literature_screening`, or `E:\wenxian\literature_screening` absolute path residues
- Confirmed the previously problematic projects still load correctly after migration:
  - project `6de7c6c79052` (`隐球菌`) still has `11` full-text queue items and `7` ready full texts
  - project `29d005d21e2c` still has `28` full-text queue items and `24` ready full texts
- Added regression coverage for relative-path persistence and config hydration in:
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_task_store.py`
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
- Added API compatibility fields so callers can read both resolved absolute paths and stored-relative paths:
  - datasets now return `path` plus `relative_path`
  - task details now return `run_root` plus `run_root_relative`
  - task details now return `output_dir` plus `output_dir_relative`
- Updated frontend API types in `/Users/mao/Documents/langchain/literature_screening_web/src/types/api.ts` to recognize the new relative-path response fields
- Refreshed the public-facing documentation so GitHub docs now match the current Docker-first runtime and thread-first workflow:
  - `/Users/mao/Documents/langchain/README.md`
  - `/Users/mao/Documents/langchain/literature_screening/docs/architecture.md`
  - `/Users/mao/Documents/langchain/literature_screening/docs/web-workbench.md`
  - `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/README.md`
- Clarified the root README so startup instructions now distinguish macOS `.command` helpers from Windows manual `docker compose -f docker-compose.local.yml up -d --build`
- Pushed the active work to `origin/codex/relative-path-api-compat`, so the current thread can be resumed from a remote branch instead of only local workspace state
- Current tracked worktree is effectively clean; remaining local-only items are untracked environment artifacts such as `.DS_Store`, `.venv/`, and `firstagent/`
- Added a reusable Codex skill for future thread handoff updates at `/Users/mao/.codex/skills/project-handoff-sync/SKILL.md`
- Added persisted thread-level workflow context in project metadata so each thread can now store:
  - research need
  - selected search databases
  - latest generated strategy plan
  - default screening topic and criteria
  - default screening model and batch settings
- Added `PUT /api/projects/{project_id}/workflow` so the thread page can edit its fixed topic and criteria instead of only editing name/topic/description text
- Updated strategy-task creation so new-thread kickoff can start from a fuzzy requirement without requiring a manually written project topic up front
- Updated strategy-task completion so the generated screening topic and criteria are written back into the owning thread as the new defaults
- Added a new screening-review API endpoint for direct multi-select batch review overrides:
  - `/api/tasks/{task_id}/review-overrides/selection`
- Reworked the main frontend information architecture:
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/StrategyRunView.vue` is now the thread kickoff page used by `/threads/new`
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue` now uses a fixed thread-context header plus four explicit stages: thread plan, screening, full text, report
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ScreeningRunView.vue` now centers on thread/source selection, input files, and minimal run settings
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue` no longer promotes report generation directly from screening results
- Reworked screening-results interaction:
  - `/Users/mao/Documents/langchain/literature_screening_web/src/components/ScreeningRecordsTable.vue` now supports multi-select rows
  - screening records can now be filtered by year and sorted by year ascending or descending
  - screening detail supports direct batch review on selected rows in addition to title/reference-list text matching
- Verified the frontend with a Dockerized Node 20 toolchain because this shell still lacks local `node` / `npm`
- Added a dedicated hot-reload development runtime for iterative UI and API work:
  - `/Users/mao/Documents/langchain/docker-compose.dev.yml`
  - `/Users/mao/Documents/langchain/start-wenxian-dev.command`
  - `/Users/mao/Documents/langchain/stop-wenxian-dev.command`
  - `/Users/mao/Documents/langchain/literature_screening_web/vite.config.ts` now accepts env-driven proxy and HMR settings for Dockerized Vite
- Updated the stable macOS launcher to explicitly describe itself as the build-based mode and to stop the dev stack before starting, avoiding port conflicts
- Further refined the thread-first routing so thread-internal actions no longer ask the user to re-select the current thread:
  - added thread-scoped routes for plan refresh and screening kickoff under `/threads/:projectId/plan/new` and `/threads/:projectId/screening/new`
  - updated thread detail, task detail, dashboard, and sidebar draft links so they route back into the owning thread instead of bouncing users through the global screening picker
  - simplified the global screening entry so it only continues an existing thread and no longer implies that a new thread should be created from inside the screening page
- Tightened the post-screening workflow around confidence and final review:
  - screening record tables now default to relevance-first ordering and keep relevance as the secondary key when sorting by year
  - full-text workspace now acts as a combined “全文获取与最终复核” page with a dedicated `excluded` status for final review drops
  - full-text queue items now surface screening confidence and review reason so final curation can happen without bouncing back to the screening task page
- Refined that merged post-screening workflow into a clearer unified review workspace:
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue` now uses one unified candidate stream instead of two tabs; the right-side panel switches between single-record mode, batch mode, and reference-list batch matching based on what the user selected
  - the unified candidate rows now surface screening decision, confidence, and full-text state together, so the user no longer sees the screening table duplicated into a second page
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue` now acts as a screening summary page that highlights this round's source, criteria, outputs, and next actions instead of duplicating the record review table
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue` still points users into the unified review workspace as stage 3 of the thread workflow
- Further refined the homepage and thread navigation affordances:
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/DashboardView.vue` now uses a denser, more balanced homepage layout
  - `/Users/mao/Documents/langchain/literature_screening_web/src/layouts/AppShell.vue` now highlights the active thread, sorts recent threads by update time, and supports right-click open/edit/delete actions in the sidebar
- Tightened the new-thread kickoff and strategy localization flow:
  - `/Users/mao/Documents/langchain/literature_screening_web/src/views/StrategyRunView.vue` no longer auto-restores the last local strategy draft into a supposedly blank “新建线程” page; it now starts empty and offers explicit restore / clear actions when an old draft exists
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/strategy/prompt_builder.py` now explicitly requires Chinese `topic`, `intent_summary`, `screening_topic`, inclusion/exclusion criteria, notes, and CNKI concept rows, while keeping Scopus / WoS / PubMed search syntax in English
  - `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py` now writes the generated strategy back into the owning thread more aggressively: the generated Chinese `topic` becomes the thread `name`, the generated Chinese `intent_summary` becomes the thread description, and the generated Chinese `screening_topic` remains the default screening topic
  - `/Users/mao/Documents/langchain/literature_screening/tests/test_strategy_module.py` and `/Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py` now cover the new prompt language rules and the post-strategy thread rename / description update behavior

## Known Issues

- The on-disk storage format is now relative, and the API now returns both resolved absolute paths and companion relative-path fields on dataset and task-detail responses; absolute fields are still the compatibility default
- The Docker image does not include the repository `tests/` directory, so full repo test runs are currently easier from the host environment than from inside the container
- The current shell environment still does not have local `node` / `npm` on `PATH`; frontend build verification now works through `docker run ... node:20`, but that is slower than a local toolchain
- The new dev runtime avoids rebuilds for normal source edits, but dependency changes still require a manual rebuild or fresh container startup so Python and Node dependencies can be reinstalled
- The unified review workspace currently lives in a single large frontend file (`/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue`), so a later split into smaller review-stream and action-panel components would make further UI iteration safer
- The root `README.md` now documents manual Windows startup, but the repo still does not ship a Windows-specific one-click start/stop wrapper alongside the macOS `.command` files
- `/Users/mao/Documents/langchain/literature_screening/README.md` still contains older environment notes and was not refreshed in this pass
- If future features persist new path-like fields outside the current helper keys, `storage_paths.py` and the migration script will need to be extended
- The repo can still look dirty across threads because of local untracked environment artifacts, so file-level inspection remains necessary before assuming an untracked file belongs to the current task
- Older imported projects may not all have manually curated `thread_profile` content yet; the API derives sensible defaults from existing strategy/screening history, but a dedicated one-off migration could make those defaults more explicit on disk
- Older threads whose strategy plans were generated before the 2026-04-10 localization update will keep their previous mixed-language topic / summary / criteria until the user regenerates the thread strategy once

## Next Thread Suggestions

1. Continue on `codex/relative-path-api-compat` unless the next thread intentionally needs a different branch
2. Decide whether to add an explicit migration that writes derived `thread_profile` data into all older project JSON files instead of deriving it on read
3. Consider reducing the frontend production bundle size warning by adding manual chunking or more route-level splitting
4. Break `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue` into smaller review/full-text subcomponents once the interaction model stabilizes
5. If mobile parity matters, add a visible “more” affordance for sidebar recent-thread context actions instead of relying only on right click
6. If Windows convenience matters, add PowerShell start/stop wrappers that mirror the existing macOS `.command` scripts
7. Refresh `/Users/mao/Documents/langchain/literature_screening/README.md` later so nested docs match the now-updated root README and architecture docs

## Key Files

Backend and persistence:

- `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/storage_paths.py`
- `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py`
- `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/schemas.py`
- `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/task_store.py`
- `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/workspace_store.py`
- `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/core/config.py`
- `/Users/mao/Documents/langchain/literature_screening/src/literature_screening/studio/service.py`
- `/Users/mao/Documents/langchain/literature_screening_web/src/types/api.ts`
- `/Users/mao/Documents/langchain/literature_screening_web/src/api/client.ts`
- `/Users/mao/Documents/langchain/literature_screening_web/src/stores/projects.ts`
- `/Users/mao/Documents/langchain/literature_screening_web/src/stores/tasks.ts`
- `/Users/mao/Documents/langchain/literature_screening_web/src/components/ScreeningRecordsTable.vue`
- `/Users/mao/Documents/langchain/literature_screening_web/src/views/StrategyRunView.vue`
- `/Users/mao/Documents/langchain/literature_screening_web/src/views/ScreeningRunView.vue`
- `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue`
- `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue`
- `/Users/mao/Documents/langchain/literature_screening/docs/architecture.md`
- `/Users/mao/Documents/langchain/literature_screening/docs/web-workbench.md`
- `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module/README.md`
- `/Users/mao/Documents/langchain/README.md`

Migration and runtime helpers:

- `/Users/mao/Documents/langchain/scripts/repair-api-runs-paths.py`
- `/Users/mao/Documents/langchain/scripts/relativize-api-runs-paths.py`
- `/Users/mao/Documents/langchain/docker-compose.local.yml`
- `/Users/mao/Documents/langchain/docker-compose.dev.yml`
- `/Users/mao/Documents/langchain/start-wenxian.command`
- `/Users/mao/Documents/langchain/stop-wenxian.command`
- `/Users/mao/Documents/langchain/start-wenxian-dev.command`
- `/Users/mao/Documents/langchain/stop-wenxian-dev.command`
- `/Users/mao/Documents/langchain/literature_screening_web/deploy/nginx.local.conf`
- `/Users/mao/Documents/langchain/literature_screening_web/vite.config.ts`
- `/Users/mao/Documents/langchain/literature_screening/Dockerfile`

Project handoff:

- `/Users/mao/Documents/langchain/project_state.md`
- `/Users/mao/Documents/langchain/project_session_log.md`
- `/Users/mao/.codex/skills/project-handoff-sync/SKILL.md`

## Verification

Verified in this round:

- `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest literature_screening/tests/test_task_store.py literature_screening/tests/test_api_app.py`
- `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest /Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py -k 'relative_path or relative_task_paths or relative-path or dataset_api_returns_absolute_and_relative_paths or task_detail_api_returns_absolute_and_relative_task_paths or workspace_store_persists_dataset_paths_relatively or load_run_config_resolves_api_runs_relative_paths_from_storage_root'`
- `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest /Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`
- `./.venv/bin/python -m compileall literature_screening/src/literature_screening/storage_paths.py literature_screening/src/literature_screening/api/task_store.py literature_screening/src/literature_screening/api/workspace_store.py literature_screening/src/literature_screening/core/config.py literature_screening/src/literature_screening/studio/service.py literature_screening/src/literature_screening/api/app.py scripts/relativize-api-runs-paths.py literature_screening/tests/test_task_store.py literature_screening/tests/test_api_app.py`
- `./.venv/bin/python scripts/relativize-api-runs-paths.py --api-runs-root /Users/mao/Documents/langchain/literature_screening/data/api_runs`
- `docker compose -f /Users/mao/Documents/langchain/docker-compose.local.yml up -d --build api`
- `docker compose -f /Users/mao/Documents/langchain/docker-compose.local.yml ps`
- `curl http://127.0.0.1:8000/api/health`
- `git diff --check README.md literature_screening/docs/architecture.md literature_screening/docs/web-workbench.md literature_screening/separated_modules/formal_report_module/README.md`
- `git push origin codex/relative-path-api-compat`
- `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest literature_screening/tests/test_api_app.py -q`
- `./.venv/bin/python -m compileall literature_screening/src/literature_screening/api/app.py literature_screening/src/literature_screening/api/schemas.py literature_screening/src/literature_screening/api/workspace_store.py literature_screening/tests/test_api_app.py`
- `docker run --rm -v /Users/mao/Documents/langchain/literature_screening_web:/work -w /work node:20 sh -lc 'npm ci >/tmp/npm-ci.log && npm run build >/tmp/npm-build.log && cat /tmp/npm-build.log'`
- `docker compose -p literature-screening-dev -f /Users/mao/Documents/langchain/docker-compose.dev.yml exec -T web npm run build`
- `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest /Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py -q`
- `git diff --check literature_screening/src/literature_screening/api/app.py literature_screening/src/literature_screening/api/schemas.py literature_screening/src/literature_screening/api/workspace_store.py literature_screening/tests/test_api_app.py literature_screening_web/src/api/client.ts literature_screening_web/src/components/ScreeningRecordsTable.vue literature_screening_web/src/layouts/AppShell.vue literature_screening_web/src/router/index.ts literature_screening_web/src/stores/drafts.ts literature_screening_web/src/stores/projects.ts literature_screening_web/src/stores/tasks.ts literature_screening_web/src/types/api.ts literature_screening_web/src/utils/strategy.ts literature_screening_web/src/views/DashboardView.vue literature_screening_web/src/views/ProjectDetailView.vue literature_screening_web/src/views/ScreeningRunView.vue literature_screening_web/src/views/StrategyRunView.vue literature_screening_web/src/views/TaskDetailView.vue`
- `git diff --check literature_screening_web/src/layouts/AppShell.vue literature_screening_web/src/views/DashboardView.vue literature_screening_web/src/views/FulltextQueueView.vue literature_screening_web/src/views/ProjectDetailView.vue literature_screening_web/src/views/TaskDetailView.vue`
- `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src ./.venv/bin/python -m pytest /Users/mao/Documents/langchain/literature_screening/tests/test_strategy_module.py /Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py -q`
- `git diff --check /Users/mao/Documents/langchain/literature_screening/src/literature_screening/strategy/prompt_builder.py /Users/mao/Documents/langchain/literature_screening/src/literature_screening/api/app.py /Users/mao/Documents/langchain/literature_screening/tests/test_strategy_module.py /Users/mao/Documents/langchain/literature_screening/tests/test_api_app.py`

## Run Shortcuts

Preferred local start:

```bash
cd /Users/mao/Documents/langchain
./start-wenxian.command
```

Preferred hot-reload dev start:

```bash
cd /Users/mao/Documents/langchain
./start-wenxian-dev.command
```

Preferred local stop:

```bash
cd /Users/mao/Documents/langchain
./stop-wenxian.command
```

Preferred hot-reload dev stop:

```bash
cd /Users/mao/Documents/langchain
./stop-wenxian-dev.command
```

Manual Docker fallback:

```bash
cd /Users/mao/Documents/langchain
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml down
```

Windows manual startup uses the same `docker-compose.local.yml` commands in PowerShell or another shell with Docker Desktop available.

## Deployment Notes

- Local development is now expected to use Docker first; macOS has committed `.command` wrappers, while Windows currently uses the same local compose file manually
- Persisted runtime data currently lives in `/Users/mao/Documents/langchain/literature_screening/data/api_runs`
- Persisted data is now stored relative to the `api_runs` root on disk, which is the main protection against future Mac / Windows path drift
- If importing older archives that still contain machine-specific absolute paths, use `repair-api-runs-paths.py` first and `relativize-api-runs-paths.py` second
- Existing cloud-deployment notes are still in `/Users/mao/Documents/langchain/deploy/cloud-server.md`

## Notes For The Next Codex Thread

- Read this file first for the current summary
- Then read the latest one or two entries in `/Users/mao/Documents/langchain/project_session_log.md`
- Continue from `codex/relative-path-api-compat` by default; latest pushed remote commit is `cc462c9`
- For local execution on this Mac, assume Docker first; for Windows, use the manual `docker compose -f docker-compose.local.yml up -d --build` flow documented in the root README
- Use `./start-wenxian-dev.command` for daily UI or API iteration; use `./start-wenxian.command` when you need the built nginx bundle behavior
- The main product flow is now explicitly: thread kickoff -> screening -> full text -> report
- `/threads/new` is now the primary thread-creation route; `/strategy/new` redirects there
- Each project now carries a persisted `thread_profile` with strategy context plus default screening topic/criteria; older projects may still rely on API-side derivation until they are re-saved
- The screening page intentionally hides most low-level model/runtime knobs; it now shows thread defaults first and only exposes minimal run settings plus optional per-round criteria override
- Screening task detail no longer offers direct report generation; the intended next step is the full-text workspace
- Screening review tables and the merged full-text workspace now default to relevance ordering; year sorting keeps relevance as the secondary order inside each year bucket
- The full-text workspace itself now defaults to year-first ordering with relevance as the secondary order, and it again supports checkbox-based bulk actions for final review
- The full-text workspace should only operate on already included records; initial-screening excluded or uncertain items stay in the screening layer, and if a later screening round marks the same paper as excluded/uncertain it is now filtered back out of the full-text queue
- For records without DOI, the full-text queue now preserves imported source links from RIS/EndNote URL fields (`UR` / `L1` / `L2` / `%U`) as the landing-page fallback, which is the current low-risk answer for many Chinese records
- The dashboard homepage has been rebalanced into a clearer hero + workflow + recent-thread layout, and sidebar recent-thread entries now support right-click actions for open, edit, and delete
- Do not assume persisted absolute paths on disk are authoritative anymore; the source of truth is now the relative path format under `api_runs`
- The root README and major docs are current, but `literature_screening/README.md` still reflects older environment instructions
- If a UI symptom looks like “data disappeared”, re-check whether the issue is a queue rebuild, a filtered source selection, or a newly introduced path field that bypassed `storage_paths.py`
