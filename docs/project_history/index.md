# Project History Index

## Purpose

This directory separates three concerns that should not be mixed into one file:

- `E:\wenxian_new\project_state.md`: the latest high-signal handoff snapshot for a new thread
- `E:\wenxian_new\project_session_log.md`: append-only session history
- `E:\wenxian_new\docs\project_history\state_snapshots\`: dated archives of previous `project_state.md` versions for later diffing and incident tracing

Use this index as the first stop when you need to answer either of these questions:

1. What is the current project state?
2. Which update likely introduced a regression or data inconsistency?

## Directory Layout

- `E:\wenxian_new\docs\project_history\index.md`
- `E:\wenxian_new\docs\project_history\state_snapshots\YYYY-MM-DD[_HHMM][_sha]_project_state.md`
- `E:\wenxian_new\docs\project_history\incident_notes\YYYY-MM-DD_short-issue-name.md`

## Update Workflow

When updating handoff records:

1. Read `E:\wenxian_new\project_state.md`
2. Read the latest relevant entries in `E:\wenxian_new\project_session_log.md`
3. Archive the current `project_state.md` into `state_snapshots\`
4. Update `project_state.md` in place with the new current-state summary
5. Append one new entry to `project_session_log.md`
6. Append one new row to the index table below
7. If the session is mainly a bug investigation or rollback, add an `incident_notes\...` file

## Reading Order For AI

For quick project continuation:

1. `E:\wenxian_new\project_state.md`
2. The latest 2–5 entries in `E:\wenxian_new\project_session_log.md`
3. This index if historical context is needed

For regression tracing:

1. This index
2. The relevant dated snapshot in `state_snapshots\`
3. The matching session log entry
4. The referenced branch / commit / verification commands

## Snapshot Index

| Date | Scope | Branch | Commit | Snapshot | Notes |
| --- | --- | --- | --- | --- | --- |
| 2026-04-15 | Windows startup flow, legacy data compatibility, doc-process redesign | `codex/thread-first-workflow-refresh` | `10a1099` | `E:\wenxian_new\docs\project_history\state_snapshots\2026-04-15_project_state.md` | First archived current-state snapshot under the new history structure; content summarizes code state through `d9c5230` |
| 2026-04-11 | Branch rename handoff snapshot | `codex/thread-first-workflow-refresh` | `f3b385c` | `E:\wenxian_new\docs\project_history\state_snapshots\2026-04-11_f3b385c_project_state.md` | Restored from git history; file content still reports `Last updated: 2026-04-10` |
| 2026-04-10 | Thread-first workflow and strategy localization handoff snapshot | `codex/thread-first-workflow-refresh` | `95bc711` | `E:\wenxian_new\docs\project_history\state_snapshots\2026-04-10_95bc711_project_state.md` | Restored from git history |
| 2026-04-10 | Pre-Windows-handoff macOS project state snapshot | `codex/thread-first-workflow-refresh` | `f3b385c` | `E:\wenxian_new\docs\project_history\state_snapshots\2026-04-10_project_state.md` | Legacy date-only snapshot restored before commit-by-commit backfill |
| 2026-04-09 | Architecture and workbench doc refresh handoff snapshot | `codex/thread-first-workflow-refresh` | `2164a2d` | `E:\wenxian_new\docs\project_history\state_snapshots\2026-04-09_2164a2d_project_state.md` | Restored from git history |
| 2026-04-09 | Relative-path persistence and API compatibility snapshot | `codex/thread-first-workflow-refresh` | `bee7205` | `E:\wenxian_new\docs\project_history\state_snapshots\2026-04-09_bee7205_project_state.md` | Restored from git history |
| 2026-04-08 | Full-text queue scoping snapshot | `codex/thread-first-workflow-refresh` | `76373b5` | `E:\wenxian_new\docs\project_history\state_snapshots\2026-04-08_76373b5_project_state.md` | Restored from git history |
| 2026-03-25 | Safe cloud update and persistent storage migration snapshot | `codex/thread-first-workflow-refresh` | `1e3c8cf` | `E:\wenxian_new\docs\project_history\state_snapshots\2026-03-25_1e3c8cf_project_state.md` | Restored from git history |
| 2026-03-25 | Dedicated workspace and report flow snapshot | `codex/thread-first-workflow-refresh` | `9b8a2f3` | `E:\wenxian_new\docs\project_history\state_snapshots\2026-03-25_9b8a2f3_project_state.md` | Restored from git history |
