---
name: update-project-state
description: Use when the user wants Codex to maintain a reusable project handoff system: a current-state summary, an append-only session log, and dated state snapshots for historical tracing. Discover or initialize the files inside the active workspace instead of relying on hardcoded paths.
---

# Update Project State

Use this skill when the user wants to:

- update project handoff notes
- keep a cross-thread state summary
- record session history for later troubleshooting
- preserve dated state snapshots so regressions can be traced by time

## Standard Structure

Prefer this layout inside the active workspace root:

- `project_state.md` — current high-signal snapshot for new threads
- `project_session_log.md` — append-only session history
- `docs/project_history/index.md` — lightweight historical index
- `docs/project_history/state_snapshots/` — dated archived copies of `project_state.md`
- `docs/project_history/incident_notes/` — optional deeper notes for bugs, migrations, or rollback analysis

If the structure does not exist and the user wants it created, initialize it in this layout.

## Discovery Rules

1. Start from the current workspace root.
2. Look for `project_state.md` and `project_session_log.md` in that workspace.
3. If they do not exist, search the current repo for the same filenames before creating new ones.
4. Use the nearest matching set that clearly belongs to the active project.
5. Do not rely on hardcoded absolute paths.

## Workflow

1. Read `project_state.md` before making conclusions about current project state.
2. Read the latest relevant entry or two from `project_session_log.md`.
3. If `docs/project_history/index.md` exists, read the latest relevant rows there too.
4. Treat `project_state.md` as the current snapshot, not as a historical log.
5. Before updating `project_state.md`, archive the previous version into `docs/project_history/state_snapshots/` using `YYYY-MM-DD[_HHMM]_project_state.md`.
6. Update `project_state.md` in place.
7. Append one new session entry to `project_session_log.md`.
8. Append one new row to `docs/project_history/index.md` when the history structure exists or is being initialized.
9. If the session mainly investigated a bug, migration, data repair, or rollback, consider adding an `incident_notes/` file.

## Content Responsibilities

### `project_state.md`

Keep it short, current, and optimized for fast AI handoff. Preserve this fixed structure:

- `Last updated`
- `Project Overview`
- `Current Product Shape`
- `This Round Changes`
- `Known Issues`
- `Next Thread Suggestions`
- `Key Files`
- `Verification`

### `project_session_log.md`

Append only. Each entry should include:

- `Scope`
- `Main changes`
- `Verification`
- `Outstanding follow-ups`
- `Files touched`

### `docs/project_history/index.md`

Keep it lightweight. Each row should help locate a historical state quickly. Prefer columns like:

- `Date`
- `Scope`
- `Branch`
- `Commit`
- `Snapshot`
- `Notes`

## Content Rules

- keep `project_state.md` as the fastest possible current summary
- keep `project_session_log.md` append-only
- keep historical snapshots immutable after creation
- separate “current state” from “historical record”
- record user-visible behavior changes, correctness fixes, migrations, important constraints, and unresolved risks
- mention only verification that actually ran
- use absolute paths for important files when it improves clickability or clarity

## Do Not

- do not turn `project_state.md` into a chronological changelog
- do not skip the snapshot archive step when materially updating `project_state.md`
- do not delete historical snapshots after creating them
- do not skip the session-log append after substantive work
- do not add low-signal terminal transcripts
- do not duplicate large amounts of code detail unless it changes future debugging decisions

## Suggested User Prompts

- `Use $update-project-state, read the current handoff files first, then update the summary, append one session log entry, and archive the previous state snapshot.`
- `Use $update-project-state and initialize a reusable handoff/history structure for this repo.`
