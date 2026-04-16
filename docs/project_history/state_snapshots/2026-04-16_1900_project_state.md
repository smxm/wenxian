# Project State

Last updated: 2026-04-15

## Project Overview

- Workspace root: `E:\wenxian_new`
- Git branch: `codex/thread-first-workflow-refresh`
- Remote tracking branch: `origin/codex/thread-first-workflow-refresh`
- Latest pushed commit: `d9c5230`
- Backend: `E:\wenxian_new\literature_screening`
- Frontend: `E:\wenxian_new\literature_screening_web`
- Runtime: Windows + Docker Desktop; dev mode uses `docker-compose.dev.yml`, build mode uses `docker-compose.local.yml`
- Product direction: thread-first literature workflow with screening, unified review/full-text handling, and report generation chained under the same thread

## Current Product Shape

Main stages:

1. Create a thread from a fuzzy research need and generate a search strategy
2. Start one or more screening rounds under that thread with inherited topic and criteria
3. Review included records in the unified screening/full-text workspace
4. Sync OA/landing-page links and mark full-text acquisition states
5. Generate reports from records marked as full-text acquired

Current behavior now in place:

- Screening imports support `.bib`, `.ris`, `.enw`, and plain-text exports
- The review workspace merges screening correction and full-text operations into one candidate stream
- Old persisted `api_runs` paths can now be resolved when data came from another machine or old workspace root
- Full-text queue rebuild prefers task outputs so original `paper_id` and imported links survive queue regeneration
- Windows now has one-click start/stop scripts for both dev and build modes

## This Round Changes

Date: 2026-04-15

- Added Windows launcher scripts in `E:\wenxian_new\start-wenxian-dev.ps1`, `E:\wenxian_new\start-wenxian.ps1`, `E:\wenxian_new\stop-wenxian-dev.ps1`, `E:\wenxian_new\stop-wenxian.ps1` and matching `.cmd` wrappers
- Hardened Docker startup checks so the scripts wait for `docker info` instead of failing on harmless warning output
- Added port probing so the web dev server can avoid common port conflicts like `8080` already being occupied
- Fixed old-project migration issues in `E:\wenxian_new\literature_screening\src\literature_screening\storage_paths.py` by remapping persisted `.../api_runs/...` Windows absolute paths into the current repository storage root
- Fixed cumulative-include and full-text queue rebuild logic in `E:\wenxian_new\literature_screening\src\literature_screening\api\workspace_store.py` so the system prefers task outputs (`deduped_records.json` and `screening_decisions.json`) and preserves original `paper_id` plus imported landing-page links
- Added RIS/paper-id compatibility support in `E:\wenxian_new\literature_screening\src\literature_screening\bibtex\parser.py`, `E:\wenxian_new\literature_screening\src\literature_screening\bibtex\exporter.py`, and `E:\wenxian_new\literature_screening\src\literature_screening\bibtex\deduper.py`
- Fixed config snapshot handling in `E:\wenxian_new\literature_screening\src\literature_screening\studio\service.py` to avoid broken input paths during reruns
- Added a small API-side project-list optimization in `E:\wenxian_new\literature_screening\src\literature_screening\api\app.py`
- Added regression tests in `E:\wenxian_new\literature_screening\tests\test_storage_paths.py` and extended `E:\wenxian_new\literature_screening\tests\test_api_app.py`
- Updated `E:\wenxian_new\README.md` and `E:\wenxian_new\literature_screening\docs\architecture.md` to document Windows startup, env precedence, old-data compatibility, and common troubleshooting
- Pushed the code changes to GitHub on `origin/codex/thread-first-workflow-refresh` at commit `d9c5230`

## Known Issues

- Docker Desktop on Windows is measurably slower than direct local Python execution for this repo, especially when reading many small files from `E:\wenxian_new\literature_screening\data\api_runs`
- `E:\wenxian_new\start-wenxian-dev.ps1` loads root `.env` first and then `E:\wenxian_new\literature_screening\.env`; the nested file overrides the root file if both define `DEEPSEEK_API_KEY` or `KIMI_API_KEY`
- If the API key inside the effective env file is invalid, strategy/report jobs fall back or fail with `401 invalid api key`
- Report generation can still look empty when model calls fail; the fallback text may show `Selected from reusable project dataset.` instead of true analysis
- Runtime artifacts under `E:\wenxian_new\literature_screening\tasks\...` remain untracked and should not be committed by default
- The current state summary had previously drifted from the real Windows workspace; it is now corrected, but future updates should keep `E:\wenxian_new` as the source of truth instead of the older macOS paths

## Next Thread Suggestions

1. If local performance matters, compare Docker mode with a direct host Python + Vite startup path and decide whether Windows daily development should default away from Docker
2. If users continue hitting invalid-key confusion, consider simplifying env loading so only one `.env` is authoritative
3. If report quality remains weak even with a valid key, inspect the report prompt and fallback note generation instead of assuming the queue logic is still wrong
4. If the unified review page keeps growing, split `E:\wenxian_new\literature_screening_web\src\views\FulltextQueueView.vue` into smaller components
5. Keep excluding `E:\wenxian_new\literature_screening\tasks\...` runtime artifacts from commits

## Key Files

- `E:\wenxian_new\README.md`
- `E:\wenxian_new\start-wenxian-dev.ps1`
- `E:\wenxian_new\start-wenxian.ps1`
- `E:\wenxian_new\stop-wenxian-dev.ps1`
- `E:\wenxian_new\stop-wenxian.ps1`
- `E:\wenxian_new\literature_screening\docs\architecture.md`
- `E:\wenxian_new\literature_screening\src\literature_screening\storage_paths.py`
- `E:\wenxian_new\literature_screening\src\literature_screening\api\app.py`
- `E:\wenxian_new\literature_screening\src\literature_screening\api\workspace_store.py`
- `E:\wenxian_new\literature_screening\src\literature_screening\bibtex\parser.py`
- `E:\wenxian_new\literature_screening\src\literature_screening\bibtex\exporter.py`
- `E:\wenxian_new\literature_screening\src\literature_screening\bibtex\deduper.py`
- `E:\wenxian_new\literature_screening\src\literature_screening\studio\service.py`
- `E:\wenxian_new\literature_screening\tests\test_api_app.py`
- `E:\wenxian_new\literature_screening\tests\test_storage_paths.py`
- `E:\wenxian_new\project_state.md`
- `E:\wenxian_new\project_session_log.md`

## Verification

Verified in this round:

- `cd E:\wenxian_new\literature_screening && cmd /c "set PYTHONPATH=E:\wenxian_new\literature_screening\src&& python -m pytest -q tests\test_storage_paths.py"`
- `cd E:\wenxian_new\literature_screening && cmd /c "set PYTHONPATH=E:\wenxian_new\literature_screening\src&& python -m pytest -q tests\test_api_app.py -k fulltext_queue"`
- `cd E:\wenxian_new && git push -u origin codex/thread-first-workflow-refresh`
