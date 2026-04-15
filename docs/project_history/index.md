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
- `E:\wenxian_new\docs\project_history\state_snapshots\YYYY-MM-DD[_HHMM]_project_state.md`
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
| 2026-04-15 | Windows startup flow, legacy data compatibility, doc-process redesign | `codex/thread-first-workflow-refresh` | `d9c5230` | `E:\wenxian_new\docs\project_history\state_snapshots\2026-04-15_project_state.md` | First archived state snapshot under the new history structure |
