# Documentation, Handoff, and Skills

## Owns

- current project handoff and append-only session history
- historical snapshot index and incident notes
- module atlas, change routing, and durable invariants
- archive policy for stale docs
- local Codex skills that help future threads maintain or navigate the project

## Main Files

| File | Responsibility |
| --- | --- |
| `project_state.md` | shortest current snapshot for a new thread |
| `project_session_log.md` | append-only chronology of substantive sessions |
| `docs/project_history/index.md` | index into immutable state snapshots and incident notes |
| `docs/project_atlas/index.md` | reading order and system layer map |
| `docs/project_atlas/change-routing.md` | feature request to likely edit-entry map |
| `docs/project_atlas/invariants.md` | stable contracts and documentation rules |
| `docs/project_atlas/modules/*.md` | module ownership cards |
| `docs/archive/legacy-docs/` | stale docs kept for context, not current truth |
| `skills/` | repo copy of reusable local skills |

## Start Here When

- a future thread needs to know where to edit before reading code
- current docs contain machine-specific absolute paths
- old docs need archiving or replacement pointers
- a reusable skill should be created or refined
- module ownership or likely edit entry points changed

## Typical Changes

- snapshot `project_state.md` before updating it
- update `project_state.md`, append to `project_session_log.md`, and add a row to `docs/project_history/index.md`
- update the relevant atlas module card and `change-routing.md`
- move stale docs into `docs/archive/legacy-docs/` instead of leaving them as primary entry points
- keep active docs workspace-relative and avoid mixing host-specific paths into reusable instructions
- mirror important skill changes into `skills/` when a project copy is useful

## Watch-Outs

- do not rewrite historical snapshots after creation
- do not edit old session-log entries just to modernize their paths
- do not let archived docs compete with `docs/project_atlas/` as the current source of truth
- if a skill lives in Codex home, update the home copy; if this repo should remember the skill, keep a repo copy under `skills/`

## Common Verifications

- path-hygiene `rg` scans over active docs, README files, deploy docs, and `skills/`
- `git diff --check`
