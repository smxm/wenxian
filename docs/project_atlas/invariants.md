# Invariants

These are the contracts that keep the current architecture coherent. Break them only on purpose.

## 1. UI "thread" is still a persisted `Project`

- The frontend uses thread language, but persistence still revolves around `project.json`.
- `thread_profile` inside the project record is the durable place for latest strategy and screening defaults.
- If this mapping changes, update both the API schemas and the view/store copy at the same time.

Touched by:
`literature_screening/src/literature_screening/api/workspace_store.py`, `api/app.py`, `api/schemas.py`, `literature_screening_web/src/views/ThreadNewView.vue`, `ProjectDetailView.vue`

## 2. `TaskStore` owns execution lifecycle and event history

- Create, retry, cancel, progress, status transitions, and event logs should flow through `TaskStore`.
- The frontend polling model depends on `status`, `phase`, `progress_*`, and `events.json` staying consistent.
- Avoid ad hoc JSON mutations in task directories that bypass `TaskStore`.

Touched by:
`literature_screening/src/literature_screening/api/task_store.py`, `api/app.py`, `studio/service.py`, `literature_screening_web/src/stores/tasks.ts`

## 3. Datasets are project-scoped and lineage matters

- A dataset belongs to one project and should preserve `task_id` plus `source_dataset_ids` whenever possible.
- Project-derived datasets such as `cumulative_included`, `fulltext_ready`, and `report_source` are project-level views, not one-off page state.
- Lookup bugs often come from accidentally treating dataset ids as globally unique business objects without project context.

Touched by:
`literature_screening/src/literature_screening/api/workspace_store.py`, `api/app.py`, `literature_screening_web/src/views/ProjectDetailView.vue`, `FulltextQueueView.vue`

## 4. Persisted disk paths are stored relative to `data/api_runs`

- Read/write code should go through `rewrite_storage_payload` and related helpers instead of manually serializing absolute paths.
- The API may still expose both absolute and relative paths for compatibility, but the disk format should remain relative-path based.
- Migration scripts exist because older data can still contain absolute paths.

Touched by:
`literature_screening/src/literature_screening/storage_paths.py`, `api/task_store.py`, `api/workspace_store.py`, `scripts/repair-api-runs-paths.py`, `scripts/relativize-api-runs-paths.py`

## 5. Frontend talks to the API surface, not directly to host paths

- Views and stores should prefer `/api/...` contracts and artifact-download endpoints.
- Do not make frontend behavior depend on local machine paths or on parsing the filesystem layout directly.
- If a new UI needs data that only exists on disk, expose it through the API layer first.

Touched by:
`literature_screening_web/src/api/client.ts`, `literature_screening_web/src/types/api.ts`, `literature_screening/src/literature_screening/api/app.py`

## 6. Screening outputs stay the downstream source of truth

- Manual review, workbench rebuilds, fulltext queues, and reports all ultimately depend on screening outputs and their derived datasets.
- If you change screening decision formats, exported files, or paper-id behavior, inspect downstream fulltext and report flows too.
- Preserve paper identity and summary counts carefully; downstream features assume they remain stable enough to reconcile records.

Touched by:
`literature_screening/src/literature_screening/bibtex/`, `screening/`, `pipeline/`, `reporting/`, `api/workspace_store.py`, `literature_screening_web/src/views/TaskDetailView.vue`

## 7. Reporting is detached, but not independent of the main product

- The detached report module is a subsystem, not a separate app.
- The main API and orchestration layer still decide when and how report tasks run.
- Report changes often require coordinated updates to request payloads, prepared screening outputs, and frontend launch surfaces.

Touched by:
`literature_screening/src/literature_screening/studio/service.py`, `reporting/`, `literature_screening/separated_modules/formal_report_module/`, `literature_screening_web/src/views/TaskDetailView.vue`, `ProjectDetailView.vue`

## 8. Docs now have separate jobs

- `project_state.md` is the shortest current snapshot.
- `project_session_log.md` and `docs/project_history/` are chronological.
- `docs/project_atlas/` is the navigation layer for module ownership and file routing.
- If one document starts doing another document's job, future threads slow down again.

## 9. Active docs use workspace-relative paths

- Current handoff, atlas, README, and skill docs should prefer repo-relative paths such as `literature_screening_web/src/views/ProjectDetailView.vue`.
- Historical snapshots and older session-log entries may keep absolute paths because they record what happened on a specific machine.
- Old explanatory docs that are no longer the primary source of truth belong under `docs/archive/legacy-docs/` with a short pointer to the current replacement.

Touched by:
`project_state.md`, `project_session_log.md`, `docs/project_history/index.md`, `docs/project_atlas/`, `docs/archive/`, `skills/`
