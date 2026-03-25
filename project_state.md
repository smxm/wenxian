# Project State

Last updated: 2026-03-25

## Repository layout

- `E:\wenxian\literature_screening`
  Main backend. FastAPI API, screening pipeline, project/task storage, deployment files.
- `E:\wenxian\literature_screening_web`
  Main Vue frontend.
- `E:\wenxian\literature_screening\separated_modules\formal_report_module`
  Independent simple report generator module used by the main app.

## Current product shape

The user-facing product is a thread-first literature workflow tool.

Main stages:

1. Generate search / screening strategy
2. Upload files and run screening
3. Manual review overrides
4. Full-text acquisition
5. Generate report

User-facing primary concept:

- `主题线程`

Internal concepts still exist:

- project
- task
- dataset / artifact

Those internal concepts are still used by the backend, but should stay as hidden as possible in the frontend.

## Stable parts

### Screening

- Input formats supported:
  - `.bib`
  - `.ris`
  - `.enw`
  - supported text exports including PubMed-style txt
- Screening pipeline supports:
  - merge
  - dedupe
  - batching
  - manual review override
  - continue from `unused`
- Default screening batch size is now `10`.

### Strategy module

- Generates:
  - Scopus advanced query
  - WoS advanced query
  - PubMed advanced query
  - CNKI advanced query lines
- Intended model:
  - DeepSeek reasoner

### Report module

- Simple report structure:
  - 文献总体情况
  - 类型划分
  - 逐篇文献总结分析
  - 参考文献列表
- Reference styles:
  - `GB/T 7714`
  - `APA7`
- Paper note generation supports incremental reuse across report tasks.

### Manual review

- Single-item review override works
- Bulk review override works
- Reviewed included / excluded RIS outputs exist
- Continue screening from unused inherits parent-round configuration
- Report source can use reviewed included records

## Recent fixes already in place

### Thread detail page

- `ProjectDetailView.vue` was rewritten after earlier corruption / encoding issues.
- Current thread page supports:
  - thread overview
  - strategy task cards
  - screening round cards
  - report cards
  - quick actions
  - report generation panel
  - full-text workspace summary / entry
- Thread header was tightened to avoid giant empty hero blocks on wide screens.
- Screening round actions now separate:
  - continue screening
  - enter full-text workspace
  - send selected round into report workspace
- Clicking the report entry from a screening card now:
  - preselects that round's included dataset
  - scrolls to the report panel
  - shows a temporary highlighted guidance state

### Sidebar / navigation

- Recent threads in the left sidebar are now fully rendered by default.
- Collapsed state means:
  - the visible height is limited to about five items
  - the user can still scroll to older threads immediately
- Expand / collapse only controls height now; it does not change which threads are rendered.
- The explanatory subtitle under "最近主题" was removed to reduce clutter.

### Report creation UX

- Backend rejects empty report sources instead of silently creating empty reports.
- Frontend validates selected report datasets and surfaces an error if the source is empty or stale.
- Report task creation now includes `project_id` from the frontend.
- Report dataset lookup is now scoped to the current project rather than relying on globally reused dataset ids.
- This fixed the bug where one project's `fulltext-ready` could incorrectly resolve to another project's empty `fulltext-ready`.

### Full-text acquisition

- Full-text queue exists at project level.
- Queue statuses:
  - `pending`
  - `ready`
  - `unavailable`
  - `deferred`
- Report source options include:
  - `仅已获取全文`
  - `项目累计纳入`
  - round-level included datasets
- Full-text workflow now has a dedicated page:
  - `E:\wenxian\literature_screening_web\src\views\FulltextQueueView.vue`
- The dedicated page supports:
  - source selection
  - queue rebuild
  - OA / link refresh
  - status chips as filters
  - keyword filtering
  - save feedback after marking items
  - temporary highlight on the updated item
- Rebuilding the queue now also correctly refreshes the derived `fulltext_ready` dataset when the source becomes empty.

## Current known state

Major correctness issues in the full-text / report bridge were fixed in this thread:

- report generation using `fulltext-ready` could resolve the wrong project's dataset because `fulltext-ready` is not globally unique
- queue rebuild and `fulltext_ready` metadata could drift when sources disappeared or changed
- report entry from screening cards lacked visible feedback and looked like "nothing happened"

Remaining work is now mostly UX polish rather than data correctness.

Likely next areas:

1. Further separate the visual language of screening / full-text / report stages
2. Continue trimming low-value explanatory copy where the UI is already self-explanatory
3. Review route-based quick actions for clearer transition feedback
4. Continue checking mobile layout for thread actions and the full-text workspace

## Useful files for the next thread

Backend:

- `E:\wenxian\literature_screening\src\literature_screening\api\app.py`
- `E:\wenxian\literature_screening\src\literature_screening\api\workspace_store.py`
- `E:\wenxian\literature_screening\src\literature_screening\studio\service.py`

Frontend:

- `E:\wenxian\literature_screening_web\src\layouts\AppShell.vue`
- `E:\wenxian\literature_screening_web\src\views\ProjectDetailView.vue`
- `E:\wenxian\literature_screening_web\src\views\FulltextQueueView.vue`
- `E:\wenxian\literature_screening_web\src\components\ThreadMessageCard.vue`
- `E:\wenxian\literature_screening_web\src\stores\projects.ts`
- `E:\wenxian\literature_screening_web\src\stores\tasks.ts`
- `E:\wenxian\literature_screening_web\src\api\client.ts`
- `E:\wenxian\literature_screening_web\src\types\api.ts`
- `E:\wenxian\literature_screening_web\src\types\thread.ts`

Report module:

- `E:\wenxian\literature_screening\separated_modules\formal_report_module\src\literature_screening\formal_report\simple_report.py`

## Suggested restart commands

Backend:

```powershell
cd E:\wenxian\literature_screening
python -m uvicorn literature_screening.api.app:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```powershell
cd E:\wenxian\literature_screening_web
npm run dev
```

## Tencent Cloud / deployment summary

Current deployment target:

- Tencent Cloud Lighthouse
- Ubuntu + Docker CE
- Public IP access with site-level Basic Auth

Current deployment shape:

- Backend:
  - FastAPI API container
- Frontend:
  - Vue app built into an Nginx container
- Runtime data:
  - persisted under `server-data/api_runs`

Important deployment files:

- `E:\wenxian\docker-compose.yml`
- `E:\wenxian\literature_screening\Dockerfile`
- `E:\wenxian\literature_screening_web\Dockerfile`
- `E:\wenxian\literature_screening_web\deploy\nginx.conf`
- `E:\wenxian\.env.deploy.example`
- `E:\wenxian\deploy\cloud-server.md`

Current operational assumptions:

- API keys are stored on the server, not exposed in frontend code
- Public access is protected by Basic Auth
- This setup is intended for small-scale use, not open anonymous public traffic

Expected server-side paths:

- project root:
  - `/opt/wenxian`
- runtime outputs:
  - `/opt/wenxian/server-data/api_runs`
- environment file:
  - `/opt/wenxian/.env`

Expected environment variables:

- `DEEPSEEK_API_KEY`
- `KIMI_API_KEY`

Network / firewall expectations:

- open:
  - `22`
  - `80`
- later, if HTTPS is added:
  - `443`

Known deployment caveat:

- Server-to-GitHub connectivity was unstable.
- The more reliable update path is:
  1. package locally
  2. upload archive to server
  3. extract in `/opt/wenxian`
  4. rebuild with Docker Compose

Recommended future additions to this state file:

- current cloud deployment status
- current update procedure
- current Basic Auth policy
- current report source defaults
- current full-text queue source / ready-set rules

## Git / repository summary

Current local repository:

- root:
  - `E:\wenxian`
- this is a Git repository used as the project root

Important branch history used in this project:

- local historical working branch:
  - `master`
- safe publish branch used before cleanup:
  - `codex/github-safe`
- release-oriented branch used for cleaned publishing:
  - `codex/release-clean`
- GitHub published branch:
  - `main`

Current remote:

- `origin`
- GitHub repository:
  - `https://github.com/smxm/wenxian.git`

Important Git decisions already made:

- API key files such as `.env` must not be committed
- deployment and runtime outputs should not be treated as source of truth
- large runtime outputs / generated reports are not intended for normal Git tracking
- cleaned release publishing was separated from raw working history

Recommended update flow for this repo:

1. make and verify local changes
2. commit locally
3. if deploying to the cloud server, package locally instead of relying on server-side `git clone`
4. upload package to server
5. rebuild containers on the server

Important caveat:

- server-side access to GitHub was unstable in practice
- direct `git clone` / `curl github.com` on the Tencent Cloud server should not be treated as reliable
- local packaging plus manual upload is the safer path right now

## Deployment update note

Important correction:

- runtime data should not depend on `/opt/wenxian/server-data/api_runs` as the only persisted location
- replacing `/opt/wenxian` during updates can otherwise wipe thread / task state if copy-forward fails

Current recommended persistent paths on the server:

- app data:
  - `/opt/wenxian-data/api_runs`
- Basic Auth file:
  - `/opt/wenxian-secrets/.htpasswd`

Current deployment config supports:

- `APP_DATA_DIR`
- `BASIC_AUTH_FILE`

Recommended update path:

1. package locally
2. upload `.tar.gz` to the server
3. run:
   - `/opt/wenxian/deploy/server-update.sh /opt/wenxian-release.tar.gz`

Local packaging helper:

- `E:\wenxian\scripts\package-release.ps1`
