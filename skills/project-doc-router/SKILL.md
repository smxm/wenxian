---
name: project-doc-router
description: "Use when the user wants Codex to quickly read the project handoff/atlas docs and identify the likely files, modules, and verification path for a requested change before editing."
---

# Project Doc Router

Use this skill when the user asks to:

- quickly locate where a change should be made
- read project docs before touching code
- find the right module, files, or owner area for a feature request
- produce a concise implementation map from existing handoff docs
- avoid re-discovering project structure from scratch

## Discovery

1. Start at the active workspace root.
2. Prefer the local handoff set if present:
   - `project_state.md`
   - `docs/project_atlas/index.md`
   - `docs/project_atlas/change-routing.md`
   - `docs/project_atlas/invariants.md`
   - `docs/project_atlas/modules/`
3. If those files are missing, search with `rg --files -g 'project_state.md' -g 'docs/project_atlas/**'`.
4. Do not rely on hardcoded absolute paths.

## Routing Workflow

1. Read `project_state.md` to understand the current product shape and known risks.
2. Read `docs/project_atlas/index.md` for the system layer map.
3. Search `docs/project_atlas/change-routing.md` for the user's feature terms.
4. Read only the relevant module cards under `docs/project_atlas/modules/`.
5. If the request involves a regression, data migration, or old behavior, then read:
   - the latest relevant entries in `project_session_log.md`
   - `docs/project_history/index.md`
   - any matching `docs/project_history/incident_notes/*.md`
6. Use `rg` in the codebase to confirm that the routed files still contain the named functions, routes, or components.

## Output Shape

For planning-only requests, answer with:

- likely start files
- secondary files to inspect if the first layer is not enough
- why those files are the right entry points
- suggested verification commands or browser flows
- any open risk or ambiguity

For implementation requests, use the routing result as the map, then continue into the code change without stopping for approval unless the user asked for planning only.

## Path Rules

- Use workspace-relative paths in notes and docs.
- Historical snapshots may contain old absolute paths; treat them as records, not current instructions.
- If a host-specific path is unavoidable, say why it is host-specific.

## Do Not

- do not read every historical snapshot by default
- do not treat archived docs under `docs/archive/` as current truth unless the user asks for old context
- do not stop at a routing answer when the user clearly asked for an implementation
- do not rewrite project docs as part of this skill unless the user asks to update documentation
