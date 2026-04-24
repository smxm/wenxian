# Workflow Orchestration

## Owns

- conversion from API payloads into runnable strategy, screening, and report jobs
- upload persistence and run-directory preparation
- shared bootstrap logic between the main project and the detached report module
- virtual screening-output preparation for report tasks launched from datasets
- partial screening-output recovery when a run is cancelled after some batches have completed

## Main Files

| File | Responsibility |
| --- | --- |
| `literature_screening/src/literature_screening/studio/service.py` | the central bridge between API requests and executable jobs |
| `literature_screening/src/literature_screening/core/` | shared config and environment helpers consumed during run setup |
| `literature_screening/separated_modules/formal_report_module/` | detached report subsystem imported by orchestration code |

## Start Here When

- the request payload looks correct but the created run root, artifacts, or prepared inputs are wrong
- uploaded files are not copied, named, or reused correctly
- report generation from project datasets fails before it even reaches the detached report module

## Typical Changes

- adjust job request dataclasses and default values
- change how uploads, criteria files, or virtual screening outputs are prepared
- wire new artifacts or markdown previews back into task payloads
- tweak bootstrap logic so the detached report module can still resolve shared code and `.env`
- preserve the effective per-run topic/criteria/model snapshot when a thread default changes later

## Watch-Outs

- `service.py` sits on the boundary between API contracts and pipeline/report code, so a small change here can ripple widely
- detached report imports depend on bootstrap path wiring; do not casually remove that path setup
- if a new feature needs long-lived persisted metadata, that probably belongs in API/storage, not only in orchestration
- target-stop and cancel-salvage behavior must still produce artifacts that downstream workbench/report code can consume

## Common Verifications

- `PYTHONPATH=/Users/mao/Documents/langchain/literature_screening/src /Users/mao/Documents/langchain/literature_screening/.venv311-codex/bin/python -m pytest literature_screening/tests/test_api_app.py`
- `python -m compileall` over `literature_screening/src/literature_screening/studio/service.py` and nearby touched files
