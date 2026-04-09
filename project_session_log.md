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
