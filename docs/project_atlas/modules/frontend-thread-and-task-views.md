# Frontend Thread and Task Views

## Owns

- the actual user-facing thread, task, screening, strategy, and fulltext experiences
- page-level composition of store data and API results
- copy, affordances, and stage-to-stage handoff inside the workbench

## Main Files

| File | Responsibility |
| --- | --- |
| `literature_screening_web/src/views/ThreadNewView.vue` | create a new thread from the research need |
| `literature_screening_web/src/views/ProjectDetailView.vue` | thread home, stage actions, project-level review/report surfaces, report source/model selectors |
| `literature_screening_web/src/views/StrategyRunView.vue` | strategy kickoff and refresh flow |
| `literature_screening_web/src/views/ScreeningRunView.vue` | screening form, source selection, provider model dropdown, and round naming |
| `literature_screening_web/src/views/TaskDetailView.vue` | task progress, review, screening edit handoff, task delete controls, stop/snapshot display, artifacts, and report launch |
| `literature_screening_web/src/views/FulltextQueueView.vue` | project-level fulltext workbench, filters, pagination, multi-select, and inline fulltext/report-source actions |
| `literature_screening_web/src/components/ScreeningRecordsTable.vue` | screening review table behavior |
| `literature_screening_web/src/components/ArtifactList.vue` | task artifact display |

## Start Here When

- the user-visible behavior is wrong on a specific page
- copy, labeling, or stage handoff feels confusing
- a route-specific interaction works in one page but not another

## Typical Changes

- reorganize page sections or action buttons
- add or remove page-specific summary blocks
- change how task detail exposes source lineage, uploaded files, or next-step suggestions
- adjust report-source selection, screening/report provider model dropdowns, or task-to-form edit handoffs
- adjust fulltext workbench layout, result pagination, one-record actions, or selected-record batch actions
- split a large view into smaller components once behavior is stable enough

## Watch-Outs

- these views are still relatively large, so trace where each piece of data really comes from before editing
- avoid duplicating business logic in the page when the API can return the right derived state directly
- keep return-to-thread navigation consistent when launching child flows from a thread
- editing a screening task currently means restoring its saved request payload into a new screening form, not mutating completed historical artifacts

## Common Verifications

- browser walkthrough of the affected page and the immediately previous/next page in the workflow
- `cd literature_screening_web && npm run typecheck`
