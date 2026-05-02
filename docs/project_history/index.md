# Project History Index

## Purpose

This directory separates the current handoff snapshot from append-only history:

- `project_state.md` — current high-signal snapshot for the next thread
- `project_session_log.md` — append-only session history
- `docs/project_history/state_snapshots/` — immutable archived copies of older `project_state.md` versions

Use this index when you need to locate the right snapshot or quickly correlate a behavior change with a date, branch, and verification record.

## Directory Layout

- `docs/project_history/index.md`
- `docs/project_history/state_snapshots/YYYY-MM-DD[_HHMM][_sha]_project_state.md`
- `docs/project_history/incident_notes/YYYY-MM-DD_short-issue-name.md`

## Update Workflow

When updating handoff records:

1. Read `project_state.md`
2. Read the latest relevant entries in `project_session_log.md`
3. Archive the current `project_state.md` into `state_snapshots/`
4. Update `project_state.md` in place
5. Append one new entry to `project_session_log.md`
6. Append one new row to the snapshot table below
7. If the session is mostly a bug investigation or rollback, consider adding an incident note

## Reading Order For AI

For quick continuation:

1. `project_state.md`
2. The latest 2–5 entries in `project_session_log.md`
3. This index if older context matters

For regression tracing:

1. This index
2. The relevant dated snapshot in `state_snapshots/`
3. The matching session log entry
4. The referenced branch, commit, and verification commands

## Snapshot Index

| Date | Scope | Branch | Commit | Snapshot | Notes |
| --- | --- | --- | --- | --- | --- |
| 2026-04-24 | Documentation path hygiene, legacy-doc archive, and project-doc-router skill | `codex/thread-first-workflow-refresh` | `58abe8b` | `docs/project_history/state_snapshots/2026-04-24_2359_project_state.md` | Normalizes active docs toward workspace-relative paths, archives old architecture/workbench notes, refreshes README/deploy docs, and adds `$project-doc-router` for fast future edit-location routing |
| 2026-04-24 | Report source selection, provider model discovery, and live screening progress | `codex/thread-first-workflow-refresh` | `58abe8b` | `docs/project_history/state_snapshots/2026-04-24_1902_project_state.md` | Adds provider `/models` discovery for report and screening model dropdowns, report-source multi-select, screening-task edit handoff, and live screening counts during batch processing |
| 2026-04-24 | Pre-push verification and handoff refresh | `codex/thread-first-workflow-refresh` | `06110bb` | `docs/project_history/state_snapshots/2026-04-24_1841_project_state.md` | Records the final pre-push verification set, including backend/report tests and direct `vue-tsc` execution through the bundled Codex Node runtime |
| 2026-04-24 | Screening/fulltext workbench refresh and simple-report taxonomy fix | `codex/thread-first-workflow-refresh` | `06110bb` | `docs/project_history/state_snapshots/2026-04-24_report-and-workbench_state.md` | Captures target-stop/manual-stop behavior, screening deletion/editing, the fulltext workbench search-platform redesign, and the `deepseek-chat` simple-report category-hint contamination fix; see `docs/project_history/incident_notes/2026-04-24_report-category-hints.md` |
| 2026-04-18 | Project atlas navigation docs and handoff redesign | `codex/thread-first-workflow-refresh` | `06110bb` | `docs/project_history/state_snapshots/2026-04-18_1430_project_state.md` | Adds `docs/project_atlas/` with module cards, change routing, and invariants so new threads can jump from feature request to likely files faster |
| 2026-04-18 | Screening naming, detail-summary cleanup, and handoff refresh | `codex/thread-first-workflow-refresh` | `06110bb` | `docs/project_history/state_snapshots/2026-04-18_1045_project_state.md` | Captures the optional custom screening-round title field, uploaded-file visibility in screening detail summaries, and removal of the redundant output/actions block |
| 2026-04-16 | Tencent Cloud update-path review and handoff refresh | `codex/thread-first-workflow-refresh` | `750ee00` | `docs/project_history/state_snapshots/2026-04-16_2358_project_state.md` | Records the current tarball-based Tencent Cloud update flow, persistent data mounts, and the missing `.env.deploy.example` caveat |
| 2026-04-16 | Report-generation diagnosis, reasoner hardening, and bibliography metadata repair | `codex/thread-first-workflow-refresh` | `750ee00` | `docs/project_history/state_snapshots/2026-04-16_1916_project_state.md` | Captures the `cd13976ef17e` investigation, `deepseek-reasoner` token-floor fix, fallback humanities taxonomy repair, and restored page metadata in project report sources |
| 2026-04-16 | Workbench stabilization, thread-first flow cleanup, report-stage polish, and handoff refresh | `codex/thread-first-workflow-refresh` | `750ee00` | `docs/project_history/state_snapshots/2026-04-16_1900_project_state.md` | Current macOS-workspace handoff refresh for shipped product changes only |
| 2026-04-15 | Windows startup flow, legacy data compatibility, and doc-process redesign | `codex/thread-first-workflow-refresh` | `10a1099` | `docs/project_history/state_snapshots/2026-04-15_project_state.md` | First archived current-state snapshot under the new history structure; content summarizes code state through `d9c5230` |
| 2026-04-11 | Branch rename handoff snapshot | `codex/thread-first-workflow-refresh` | `f3b385c` | `docs/project_history/state_snapshots/2026-04-11_f3b385c_project_state.md` | Restored from git history; file content still reports `Last updated: 2026-04-10` |
| 2026-04-10 | Thread-first workflow and strategy localization handoff snapshot | `codex/thread-first-workflow-refresh` | `95bc711` | `docs/project_history/state_snapshots/2026-04-10_95bc711_project_state.md` | Restored from git history |
| 2026-04-10 | Pre-Windows-handoff macOS project state snapshot | `codex/thread-first-workflow-refresh` | `f3b385c` | `docs/project_history/state_snapshots/2026-04-10_project_state.md` | Legacy date-only snapshot restored before commit-by-commit backfill |
| 2026-04-09 | Architecture and workbench doc refresh handoff snapshot | `codex/thread-first-workflow-refresh` | `2164a2d` | `docs/project_history/state_snapshots/2026-04-09_2164a2d_project_state.md` | Restored from git history |
| 2026-04-09 | Relative-path persistence and API compatibility snapshot | `codex/thread-first-workflow-refresh` | `bee7205` | `docs/project_history/state_snapshots/2026-04-09_bee7205_project_state.md` | Restored from git history |
| 2026-04-08 | Full-text queue scoping snapshot | `codex/thread-first-workflow-refresh` | `76373b5` | `docs/project_history/state_snapshots/2026-04-08_76373b5_project_state.md` | Restored from git history |
| 2026-03-25 | Safe cloud update and persistent storage migration snapshot | `codex/thread-first-workflow-refresh` | `1e3c8cf` | `docs/project_history/state_snapshots/2026-03-25_1e3c8cf_project_state.md` | Restored from git history |
| 2026-03-25 | Dedicated workspace and report flow snapshot | `codex/thread-first-workflow-refresh` | `9b8a2f3` | `docs/project_history/state_snapshots/2026-03-25_9b8a2f3_project_state.md` | Restored from git history |
