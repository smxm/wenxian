# Project State

Last updated: 2026-05-02 11:30 CST

## Project Overview

- Workspace root: `.`
- Git branch: `codex/thread-first-workflow-refresh`
- Backend app: `literature_screening`
- Frontend app: `literature_screening_web`
- Product direction: thread-first literature workflow from research need to strategy, screening rounds, unified review, selectable report sources, and report generation
- Recommended reading order for a new thread: `project_state.md` -> `docs/project_atlas/index.md` -> `docs/project_atlas/change-routing.md` -> the relevant module card in `docs/project_atlas/modules/`
- Fast routing skill for future threads: `$wenxian-doc-router`

## Current Product Shape

- `/threads/new` creates the thread first from the research need; follow-up work continues from the thread detail page.
- The thread detail page remains the main control surface for strategy generation, screening, unified review, fulltext workbench handoff, and report generation.
- Screening rounds can be named, edited by restoring their saved parameters into the screening form, deleted after mistakes, stopped manually without losing already processed outputs, and configured to stop automatically after a target included-paper count.
- Screening tasks now surface live batch-level counts through task summary/progress polling: processed, included, excluded, uncertain, and unused counts update after each completed batch instead of only at the end.
- Report generation can now choose one or more sources from report-source, fulltext-ready, cumulative included, and individual round included/reviewed datasets, so a newly added batch can be reported without regenerating older included batches.
- Report and screening model selection now use provider-driven dropdowns. The backend proxies provider `/models` APIs using the entered API key or server env var, with provider defaults as fallback.
- Unified review still operates at the project level with round-aware history, stable candidate identities, and report-source decisions driven by final inclusion.
- Repo navigation remains split: `project_state.md` for current status, `project_session_log.md` for chronology, `docs/project_atlas/` for module ownership plus change-entry routing, and `docs/archive/legacy-docs/` for stale docs kept only as context.

## This Round Changes

- Added provider model discovery: new `/api/model-options` endpoint that fetches model lists from provider APIs (DeepSeek, Kimi, etc.) with fallback defaults.
- Enhanced screening configuration: new parameters for `batch_size`, `target_include_count`, `stop_when_target_reached`, `min_include_confidence`, `allow_uncertain`, `retry_times`, `request_timeout_seconds`, `encoding`.
- Refactored FulltextQueueView with improved filtering, pagination, multi-select, and enrichment workflows.
- Updated ProjectDetailView, ScreeningRunView, and TaskDetailView with UI improvements and better state management.
- Added comprehensive tests for API endpoints and screening pipeline.
- Updated project atlas and module cards to reflect new provider model discovery and screening configuration features.

## Known Issues

- Starting the Vite dev server locally is currently blocked because `literature_screening_web/node_modules` is missing Rollup's macOS optional package `@rollup/rollup-darwin-arm64`; `vue-tsc` still passes through the bundled Codex Node runtime.
- Provider model discovery needs either a browser-entered API key or a server-side env var such as `DEEPSEEK_API_KEY`; otherwise the UI deliberately shows fallback defaults.
- "编辑初筛任务" restores a new editable draft from the old task. It does not mutate completed task artifacts or the historical criteria snapshot.
- Existing completed report artifacts will not rewrite themselves; rerun report tasks when a clean source selection or fresh model choice should be reflected in markdown.
- Older snapshots and earlier session-log entries still contain historical absolute paths by design; current docs and routing docs should not copy that style forward.

## Next Thread Suggestions

1. Use `$wenxian-doc-router` at the start of the next feature thread and check whether it gets to the right module card quickly enough.
2. Browser-test report generation with: report-source only, one latest included dataset only, multiple selected round datasets, and missing/invalid API key fallback.
3. Run one real long screening task and confirm the thread card plus task detail metrics update after each batch.
4. Test provider model discovery with different providers and API key configurations.
5. Repair/reinstall frontend dependencies if a local Vite server is needed; the current `node_modules` looks populated with Linux Rollup optional packages only.

## Key Files

- `project_state.md`
- `project_session_log.md`
- `docs/project_history/index.md`
- `docs/project_history/state_snapshots/2026-04-24_2359_project_state.md`
- `docs/archive/legacy-docs/README.md`
- `docs/project_atlas/change-routing.md`
- `docs/project_atlas/invariants.md`
- `docs/project_atlas/modules/backend-api-and-storage.md`
- `docs/project_atlas/modules/documentation-handoff-and-skills.md`
- `docs/project_atlas/modules/frontend-shell-and-stores.md`
- `docs/project_atlas/modules/frontend-thread-and-task-views.md`
- `docs/project_atlas/modules/reporting-and-formal-report.md`
- `docs/project_atlas/modules/screening-and-data-pipeline.md`
- `README.md`
- `deploy/cloud-server.md`
- `literature_screening/README.md`
- `literature_screening_web/README.md`
- `skills/update-project-state/SKILL.md`
- `skills/project-doc-router/SKILL.md`
- Codex home skill copy: `$CODEX_HOME/skills/project-doc-router/SKILL.md`

## Verification

- Previous code-change verification remains: backend targeted tests `8 passed, 23 deselected`, broader backend/report tests `58 passed`, frontend `vue-tsc --noEmit`, and `git diff --check`.
- Current documentation pass: active-doc path-hygiene `rg` scans returned no project absolute-path or old drive-letter matches; `find` confirmed the archived docs and new skill files; `git diff --check` passed.
