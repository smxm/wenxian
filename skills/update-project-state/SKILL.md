---
name: update-project-state
description: "Use when the user wants Codex to maintain a reusable project handoff and navigation system: a current-state summary, an append-only session log, dated state snapshots, and a project atlas for module ownership and fast change routing. Prefer workspace-relative paths in active docs."
---

# Update Project State

Use this skill when the user wants to:

- update project handoff notes
- keep a cross-thread state summary
- record session history for later troubleshooting
- preserve dated state snapshots so regressions can be traced by time
- maintain a project atlas so future threads can quickly locate the right module and files

## Standard Structure

Prefer this layout inside the active workspace root:

- `project_state.md` — current high-signal snapshot for new threads
- `project_session_log.md` — append-only session history
- `docs/project_history/index.md` — lightweight historical index
- `docs/project_history/state_snapshots/` — dated archived copies of `project_state.md`
- `docs/project_history/incident_notes/` — optional deeper notes for bugs, migrations, or rollback analysis
- `docs/project_atlas/index.md` — project navigation layer for module ownership and reading order
- `docs/project_atlas/change-routing.md` — maps common requests to likely files and downstream modules
- `docs/project_atlas/invariants.md` — durable architectural contracts and boundaries
- `docs/project_atlas/modules/` — per-module cards for ownership, entry points, risks, and verification

If the structure does not exist and the user wants it created, initialize it in this layout.

## Discovery Rules

1. Start from the current workspace root.
2. Look for `project_state.md` and `project_session_log.md` in that workspace.
3. If they do not exist, search the current repo for the same filenames before creating new ones.
4. Look for `docs/project_atlas/` in the same project before creating a new atlas.
5. Use the nearest matching set that clearly belongs to the active project.
6. Do not rely on hardcoded absolute paths.

## When To Initialize The Atlas

Create or expand `docs/project_atlas/` when any of these are true:

- the repo has multiple modules, packages, apps, or layers
- new threads would otherwise struggle to answer “where should I start editing?”
- the user asks for faster future orientation, handoff, or code-location help
- module ownership, routing, or cross-module dependencies changed in a meaningful way

For a tiny single-file or very small repo, keep the atlas minimal instead of forcing heavy structure.

## Workflow

1. Read `project_state.md` before making conclusions about current project state.
2. Read the latest relevant entry or two from `project_session_log.md`.
3. If `docs/project_history/index.md` exists, read the latest relevant rows there too.
4. If `docs/project_atlas/index.md` exists, read it before deciding how the project is organized.
5. If `docs/project_atlas/change-routing.md`, `docs/project_atlas/invariants.md`, or relevant module cards exist, read the parts that match the current task.
6. Treat `project_state.md` as the current snapshot, not as a historical log and not as the main module map.
7. Before updating `project_state.md`, archive the previous version into `docs/project_history/state_snapshots/` using `YYYY-MM-DD[_HHMM]_project_state.md`.
8. Update `project_state.md` in place.
9. Append one new session entry to `project_session_log.md`.
10. Append one new row to `docs/project_history/index.md` when the history structure exists or is being initialized.
11. If the atlas exists or should exist now, update the relevant atlas files in the same session.
12. If the session mainly investigated a bug, migration, data repair, or rollback, consider adding an `incident_notes/` file.

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

### `docs/project_atlas/index.md`

Use this as the durable navigation layer. Prefer sections such as:

- purpose of the atlas
- reading order for a new thread
- major system layers or modules
- cross-module flows
- links to module cards

### `docs/project_atlas/change-routing.md`

Keep it practical and scan-friendly. It should answer:

- “I want to change X; where do I start?”
- “Which files usually move together?”
- “What should I verify after editing this area?”

### `docs/project_atlas/invariants.md`

Record stable architectural constraints, for example:

- domain-model boundaries
- persistence contracts
- path/storage rules
- frontend/backend contracts
- workflow assumptions that downstream features rely on

### `docs/project_atlas/modules/*.md`

Each module card should stay concise and help future threads jump in quickly. Prefer sections like:

- what the module owns
- main files
- start-here triggers
- typical changes
- watch-outs
- common verification

## Content Rules

- keep `project_state.md` as the fastest possible current summary
- keep `project_session_log.md` append-only
- keep historical snapshots immutable after creation
- separate “current state” from “historical record” and from “navigation map”
- use `docs/project_atlas/` as the place for durable module ownership and change routing
- record user-visible behavior changes, correctness fixes, migrations, important constraints, and unresolved risks
- mention only verification that actually ran
- prefer workspace-relative paths in current docs, README files, atlas cards, and history indexes
- use host-specific absolute paths only when they are required for an external runtime, and explain why
- update only the atlas files affected by the session; do not rewrite the whole atlas every time
- if a feature changed ownership boundaries or the likely edit entry point, update the relevant module card and `change-routing.md` in the same session

## Do Not

- do not turn `project_state.md` into a chronological changelog
- do not skip the snapshot archive step when materially updating `project_state.md`
- do not delete historical snapshots after creating them
- do not skip the session-log append after substantive work
- do not add low-signal terminal transcripts
- do not duplicate large amounts of code detail unless it changes future debugging decisions
- do not let the atlas become a second session log
- do not maintain giant file inventories with no routing value
- do not describe module ownership vaguely if you can point to concrete entry files
- do not rewrite immutable historical snapshots or old session-log entries only to normalize paths; document the current rule instead

## Suggested User Prompts

- `Use $update-project-state, read the current handoff and atlas files first, then update the summary, atlas, session log, and history snapshot.`
- `Use $update-project-state and initialize a reusable handoff/history/atlas structure for this repo.`
- `Use $update-project-state and refresh the module map so future threads can quickly find where to edit.`
