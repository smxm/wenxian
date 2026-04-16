# Project History Index

## Purpose

This directory separates the current handoff snapshot from append-only history:

- `/Users/mao/Documents/langchain/project_state.md` — current high-signal snapshot for the next thread
- `/Users/mao/Documents/langchain/project_session_log.md` — append-only session history
- `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/` — immutable archived copies of older `project_state.md` versions

Use this index when you need to locate the right snapshot or quickly correlate a behavior change with a date, branch, and verification record.

## Directory Layout

- `/Users/mao/Documents/langchain/docs/project_history/index.md`
- `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/YYYY-MM-DD[_HHMM][_sha]_project_state.md`
- `/Users/mao/Documents/langchain/docs/project_history/incident_notes/YYYY-MM-DD_short-issue-name.md`

## Update Workflow

When updating handoff records:

1. Read `/Users/mao/Documents/langchain/project_state.md`
2. Read the latest relevant entries in `/Users/mao/Documents/langchain/project_session_log.md`
3. Archive the current `project_state.md` into `state_snapshots/`
4. Update `project_state.md` in place
5. Append one new entry to `project_session_log.md`
6. Append one new row to the snapshot table below
7. If the session is mostly a bug investigation or rollback, consider adding an incident note

## Reading Order For AI

For quick continuation:

1. `/Users/mao/Documents/langchain/project_state.md`
2. The latest 2–5 entries in `/Users/mao/Documents/langchain/project_session_log.md`
3. This index if older context matters

For regression tracing:

1. This index
2. The relevant dated snapshot in `state_snapshots/`
3. The matching session log entry
4. The referenced branch, commit, and verification commands

## Snapshot Index

| Date | Scope | Branch | Commit | Snapshot | Notes |
| --- | --- | --- | --- | --- | --- |
| 2026-04-16 | Tencent Cloud update-path review and handoff refresh | `codex/thread-first-workflow-refresh` | `750ee00` | `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-16_2358_project_state.md` | Records the current tarball-based Tencent Cloud update flow, persistent data mounts, and the missing `.env.deploy.example` caveat |
| 2026-04-16 | Report-generation diagnosis, reasoner hardening, and bibliography metadata repair | `codex/thread-first-workflow-refresh` | `750ee00` | `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-16_1916_project_state.md` | Captures the `cd13976ef17e` investigation, `deepseek-reasoner` token-floor fix, fallback humanities taxonomy repair, and restored page metadata in project report sources |
| 2026-04-16 | Workbench stabilization, thread-first flow cleanup, report-stage polish, and handoff refresh | `codex/thread-first-workflow-refresh` | `750ee00` | `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-16_1900_project_state.md` | Current macOS-workspace handoff refresh for shipped product changes only |
| 2026-04-15 | Windows startup flow, legacy data compatibility, and doc-process redesign | `codex/thread-first-workflow-refresh` | `10a1099` | `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-15_project_state.md` | First archived current-state snapshot under the new history structure; content summarizes code state through `d9c5230` |
| 2026-04-11 | Branch rename handoff snapshot | `codex/thread-first-workflow-refresh` | `f3b385c` | `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-11_f3b385c_project_state.md` | Restored from git history; file content still reports `Last updated: 2026-04-10` |
| 2026-04-10 | Thread-first workflow and strategy localization handoff snapshot | `codex/thread-first-workflow-refresh` | `95bc711` | `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-10_95bc711_project_state.md` | Restored from git history |
| 2026-04-10 | Pre-Windows-handoff macOS project state snapshot | `codex/thread-first-workflow-refresh` | `f3b385c` | `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-10_project_state.md` | Legacy date-only snapshot restored before commit-by-commit backfill |
| 2026-04-09 | Architecture and workbench doc refresh handoff snapshot | `codex/thread-first-workflow-refresh` | `2164a2d` | `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-09_2164a2d_project_state.md` | Restored from git history |
| 2026-04-09 | Relative-path persistence and API compatibility snapshot | `codex/thread-first-workflow-refresh` | `bee7205` | `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-09_bee7205_project_state.md` | Restored from git history |
| 2026-04-08 | Full-text queue scoping snapshot | `codex/thread-first-workflow-refresh` | `76373b5` | `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-04-08_76373b5_project_state.md` | Restored from git history |
| 2026-03-25 | Safe cloud update and persistent storage migration snapshot | `codex/thread-first-workflow-refresh` | `1e3c8cf` | `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-03-25_1e3c8cf_project_state.md` | Restored from git history |
| 2026-03-25 | Dedicated workspace and report flow snapshot | `codex/thread-first-workflow-refresh` | `9b8a2f3` | `/Users/mao/Documents/langchain/docs/project_history/state_snapshots/2026-03-25_9b8a2f3_project_state.md` | Restored from git history |
