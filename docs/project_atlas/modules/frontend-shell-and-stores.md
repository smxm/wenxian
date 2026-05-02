# Frontend Shell and Stores

## Owns

- route definitions and top-level navigation
- API client calls and frontend type contracts
- task polling, project loading, and local draft persistence
- app-level state that is shared across multiple views

## Main Files

| File | Responsibility |
| --- | --- |
| `literature_screening_web/src/router/index.ts` | route map and redirects |
| `literature_screening_web/src/api/client.ts` | REST client wrappers, including task/fulltext batch actions and provider model discovery |
| `literature_screening_web/src/types/api.ts` | frontend-side API types |
| `literature_screening_web/src/stores/projects.ts` | project detail, templates, workbench, fulltext actions, and report-source synchronization |
| `literature_screening_web/src/stores/tasks.ts` | task list, polling, retry, cancel, delete, edit, and review actions |
| `literature_screening_web/src/stores/drafts.ts` | localStorage-backed strategy, screening, and report drafts |
| `literature_screening_web/src/layouts/AppShell.vue` | app chrome and shared shell behavior |

## Start Here When

- a route, redirect, or back-navigation flow is wrong
- a page shows stale data because a store action or poll cycle is wrong
- a new API field exists but the page still does not receive it
- draft persistence or restored form defaults behave strangely
- report model/source selections need to survive route handoffs and local draft restores

## Typical Changes

- add or revise route params
- update store actions after API changes
- propagate new response fields into `types/api.ts`
- adjust draft reset and hydrate behavior
- add typed client wrappers when the backend exposes model/provider metadata or new task payloads
- keep selected-record and paginated fulltext state in the view, while persisting durable status/report-source changes through the store/API

## Watch-Outs

- a large amount of "page logic" actually lives in the stores, so do not assume a view-only fix is enough
- store changes can affect multiple pages at once
- if an API response changes, make the type update first so breakage surfaces quickly
- API keys are browser-local draft state; provider model discovery should pass them only through the API request and not persist them into task request payloads

## Common Verifications

- `cd literature_screening_web && npm run typecheck`
- browser flow across affected pages with route-param changes
