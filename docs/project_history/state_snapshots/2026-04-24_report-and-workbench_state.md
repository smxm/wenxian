# Project State

Last updated: 2026-04-18 14:30 CST

## Project Overview

- Workspace root: `/Users/mao/Documents/langchain`
- Git branch: `codex/thread-first-workflow-refresh`
- Current HEAD: `06110bb`
- Backend app: `/Users/mao/Documents/langchain/literature_screening`
- Frontend app: `/Users/mao/Documents/langchain/literature_screening_web`
- Product direction: thread-first literature workflow from research need to strategy, screening rounds, unified review, and report generation
- Recommended reading order for a new thread: `/Users/mao/Documents/langchain/project_state.md` -> `/Users/mao/Documents/langchain/docs/project_atlas/index.md` -> `/Users/mao/Documents/langchain/docs/project_atlas/change-routing.md` -> the relevant module card in `/Users/mao/Documents/langchain/docs/project_atlas/modules/` -> `/Users/mao/Documents/langchain/project_session_log.md` only if older chronology still matters

## Current Product Shape

- `/threads/new` creates the thread first from the research need; follow-up work continues from the thread detail page.
- The thread detail page remains the main control surface for strategy generation, screening, unified review, and report generation.
- The screening creation page now supports an optional custom round name; leaving it blank still falls back to `线程名-round-N`.
- The screening detail page now shows both source lineage and any uploaded file names in the round summary, making it easier to recognize which batch a run came from.
- The screening detail page has been simplified by removing the redundant “本轮产出与后续动作” block; the unified-review handoff remains the primary next step.
- Unified review still operates at the project level with round-aware history, stable candidate identities, and report-source decisions driven by final inclusion.
- Repo navigation is now split: `project_state.md` for current status, `project_session_log.md` for chronology, and `/Users/mao/Documents/langchain/docs/project_atlas/` for module ownership plus change-entry routing.

## This Round Changes

- Created `/Users/mao/Documents/langchain/docs/project_atlas/index.md` as a durable project-navigation layer so new threads can orient by module and change-entry point instead of by chronology alone.
- Added `/Users/mao/Documents/langchain/docs/project_atlas/change-routing.md`, `/Users/mao/Documents/langchain/docs/project_atlas/invariants.md`, and module cards under `/Users/mao/Documents/langchain/docs/project_atlas/modules/` for the main backend, frontend, reporting, and runtime slices.
- Updated `/Users/mao/Documents/langchain/README.md` and this state file so future threads are directed into the atlas before digging through `project_session_log.md`.
- Archived the previous handoff snapshot into `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-18_1430_project_state.md` and refreshed the history index for the documentation-system redesign.

## Known Issues

- The shared `/Users/mao/.codex/skills/update-project-state/SKILL.md` file still describes only the state/session/history structure; atlas maintenance is documented in-repo but not yet automated in the shared skill.
- Frontend build and typecheck still could not run locally because this machine does not have `npm`.
- Real browser validation is still needed for the new custom screening-name flow and the revised screening detail summary.
- Older screening tasks that do not have `request_payload.uploaded_file_names` recorded will not be able to show uploaded file names in the detail summary.
- `/Users/mao/Documents/langchain/literature_screening_web/src/views/ProjectDetailView.vue`, `/Users/mao/Documents/langchain/literature_screening_web/src/views/FulltextQueueView.vue`, and `/Users/mao/Documents/langchain/literature_screening_web/src/views/TaskDetailView.vue` are still fairly large and remain good candidates for component splitting.
- The atlas will only stay useful if future sessions update the affected module card and change-routing row when module ownership changes.

## Next Thread Suggestions

1. When the next feature touches a stable part of the product, update the matching file in `/Users/mao/Documents/langchain/docs/project_atlas/modules/` and one row in `/Users/mao/Documents/langchain/docs/project_atlas/change-routing.md` in the same session.
2. If you want this workflow standardized across future Codex runs, update `/Users/mao/.codex/skills/update-project-state/SKILL.md` so the skill explicitly maintains `docs/project_atlas/` alongside the historical handoff files.
3. Run frontend `typecheck` / build on a machine with `node` and `npm`, then use the atlas to split the largest views into smaller focused components.
4. Browser-test a real thread by creating one named screening round and one unnamed screening round, then confirm the thread page and detail page both surface the chosen title cleanly.

## Key Files

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

## Verification

- `git -C /Users/mao/Documents/langchain diff --check -- README.md project_state.md project_session_log.md docs/project_history/index.md docs/project_atlas/index.md docs/project_atlas/change-routing.md docs/project_atlas/invariants.md docs/project_atlas/modules/backend-api-and-storage.md docs/project_atlas/modules/workflow-orchestration.md docs/project_atlas/modules/screening-and-data-pipeline.md docs/project_atlas/modules/strategy-generation.md docs/project_atlas/modules/reporting-and-formal-report.md docs/project_atlas/modules/frontend-shell-and-stores.md docs/project_atlas/modules/frontend-thread-and-task-views.md docs/project_atlas/modules/runtime-and-operations.md`
- `find /Users/mao/Documents/langchain/docs/project_atlas -maxdepth 2 -type f | sort`
- `rg -n "Reading Order|Change Routing|Invariants|Module Cards" /Users/mao/Documents/langchain/docs/project_atlas/index.md /Users/mao/Documents/langchain/docs/project_atlas/change-routing.md /Users/mao/Documents/langchain/docs/project_atlas/invariants.md`
- `node -v` -> `v24.14.0`
- `npm -v` -> `command not found`
