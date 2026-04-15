# Project State

Last updated: 2026-04-09

## Project Overview

- Workspace root: `/Users/mao/Documents/langchain`
- Git branch: `main`
- Synced base commit before this round: `d58eacb`
- Backend: `/Users/mao/Documents/langchain/literature_screening`
- Frontend: `/Users/mao/Documents/langchain/literature_screening_web`
- Report module: `/Users/mao/Documents/langchain/literature_screening/separated_modules/formal_report_module`
- Local runtime: Docker-based on macOS, with API on `http://127.0.0.1:8000` and web UI on `http://127.0.0.1:8080`
- Product direction: thread-first literature workflow, with the thread object as the main user-facing concept and project/task/dataset kept mostly hidden in the UI
- Current imported workspace snapshot: `54` projects are visible through the local API

## Current Product Shape

Main stages:

1. Generate search / screening strategy
2. Upload files and run screening
3. Manual review overrides
4. Full-text acquisition
5. Generate report

Core capabilities already in place:

- Screening pipeline supports merge, dedupe, batching, manual review override, and continue-from-unused
- Supported import formats include `.bib`, `.ris`, `.enw`, and text exports such as PubMed-style txt
- Strategy generation supports Scopus, WoS, PubMed, and CNKI query output
- Full-text workflow has a dedicated page with source selection, queue rebuild, OA/link refresh, filtering, and item status updates
- Report generation supports `GB/T 7714` and `APA7`, and paper-note reuse across report tasks
- Persisted task and dataset metadata now stores `api_runs`-relative paths on disk and resolves them back to absolute paths at runtime

## This Round Changes

Date: 2026-04-09

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
- Added a reusable Codex skill for future thread handoff updates at `/Users/mao/.codex/skills/project-handoff-sync/SKILL.md`

## Known Issues

- The on-disk storage format is now relative, and the API now returns both resolved absolute paths and companion relative-path fields on dataset and task-detail responses; absolute fields are still the compatibility default
- The Docker image does not include the repository `tests/` directory, so full repo test runs are currently easier from the host environment than from inside the container
- The current shell environment does not have `npm` on `PATH`, so frontend `typecheck` was not rerun in this pass
- If future features persist new path-like fields outside the current helper keys, `storage_paths.py` and the migration script will need to be extended
- The repo can still be dirty across threads, so file-level inspection remains necessary before assuming a local modification belongs to the current task

## Next Thread Suggestions

1. Decide when API consumers can adopt `relative_path`, `run_root_relative`, and `output_dir_relative`, then plan a gradual deprecation of absolute-only assumptions
2. Keep an eye on any new persisted JSON or YAML files and route new path fields through `storage_paths.py`
3. Consider a tiny UI recovery action or admin helper for “rebuild imported full-text queue” if more migration edge cases appear
4. If cross-machine data moves continue, decide whether `repair-api-runs-paths.py` is still needed once all persisted data is relative
5. Reuse `$project-handoff-sync` whenever a substantive thread ends, so these handoff docs stay current

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

Migration and runtime helpers:

- `/Users/mao/Documents/langchain/scripts/repair-api-runs-paths.py`
- `/Users/mao/Documents/langchain/scripts/relativize-api-runs-paths.py`
- `/Users/mao/Documents/langchain/docker-compose.local.yml`
- `/Users/mao/Documents/langchain/start-wenxian.command`
- `/Users/mao/Documents/langchain/stop-wenxian.command`
- `/Users/mao/Documents/langchain/literature_screening_web/deploy/nginx.local.conf`
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

## Run Shortcuts

Preferred local start:

```bash
cd /Users/mao/Documents/langchain
./start-wenxian.command
```

Preferred local stop:

```bash
cd /Users/mao/Documents/langchain
./stop-wenxian.command
```

Manual Docker fallback:

```bash
cd /Users/mao/Documents/langchain
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml down
```

## Deployment Notes

- Local development is now expected to use Docker on macOS unless the environment is explicitly changed
- Persisted runtime data currently lives in `/Users/mao/Documents/langchain/literature_screening/data/api_runs`
- Persisted data is now stored relative to the `api_runs` root on disk, which is the main protection against future Mac / Windows path drift
- If importing older archives that still contain machine-specific absolute paths, use `repair-api-runs-paths.py` first and `relativize-api-runs-paths.py` second
- Existing cloud-deployment notes are still in `/Users/mao/Documents/langchain/deploy/cloud-server.md`

## Notes For The Next Codex Thread

- Read this file first for the current summary
- Then read the latest one or two entries in `/Users/mao/Documents/langchain/project_session_log.md`
- For local execution on this Mac, assume Docker first
- Do not assume persisted absolute paths on disk are authoritative anymore; the source of truth is now the relative path format under `api_runs`
- If a UI symptom looks like “data disappeared”, re-check whether the issue is a queue rebuild, a filtered source selection, or a newly introduced path field that bypassed `storage_paths.py`
