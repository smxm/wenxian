# Backend API and Storage

## Owns

- FastAPI routes and request/response contracts
- task, project, dataset, template, and secret persistence
- workbench and fulltext project-level derived state
- path hydration/dehydration around `data/api_runs`

## Main Files

| File | Responsibility |
| --- | --- |
| `literature_screening/src/literature_screening/api/app.py` | HTTP entry point and route wiring |
| `literature_screening/src/literature_screening/api/schemas.py` | request and response models shared with the frontend |
| `literature_screening/src/literature_screening/api/task_store.py` | task lifecycle, progress, retries, events, and JSON persistence |
| `literature_screening/src/literature_screening/api/workspace_store.py` | projects, datasets, cumulative included, fulltext queue, workbench state, and report-source rebuilds |
| `literature_screening/src/literature_screening/api/template_store.py` | saved task templates |
| `literature_screening/src/literature_screening/api/secret_store.py` | environment-backed secret references |
| `literature_screening/src/literature_screening/storage_paths.py` | stored-relative path compatibility helpers |

## Start Here When

- an API response shape is wrong
- a new UI field needs persisted support
- provider model discovery, task progress summaries, or report-source request payloads need API support
- dataset lineage, task metadata, or workbench state looks inconsistent
- fulltext or report-source state survives incorrectly across refreshes

## Typical Changes

- add or adjust an API endpoint in `app.py`
- extend a response model in `schemas.py`
- proxy provider metadata such as model lists through API endpoints instead of exposing provider calls directly from the browser
- carry new metadata through `TaskStore` or `WorkspaceStore`
- fix path serialization so old and new data both hydrate correctly
- keep cancellation, deletion, and dataset rebuild paths aligned so partial screening outputs do not disappear or keep polluting downstream queues

## Watch-Outs

- route ordering matters for overlapping single-item and batch endpoints
- backend schema changes usually require matching edits in `literature_screening_web/src/types/api.ts` and the relevant store/view
- if dataset lookup is wrong, check whether project scope was lost
- report tasks may seed/reuse note caches, so cache version changes must match the detached report module
- keep compatibility fields deliberate when touching path-related payloads
- live screening counts depend on both pipeline `run_summary.json` writes and API-side task summary hydration

## Common Verifications

- `PYTHONPATH=literature_screening/src python -m pytest literature_screening/tests/test_api_app.py literature_screening/tests/test_task_store.py`
- targeted `git diff --check` on touched backend files
