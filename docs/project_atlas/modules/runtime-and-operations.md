# Runtime and Operations

## Owns

- local Docker startup modes
- platform convenience scripts
- deployment/update scripts
- path-repair and data-migration helpers

## Main Files

| File | Responsibility |
| --- | --- |
| `README.md` | top-level operator entry point |
| `docker-compose.local.yml` | stable local runtime |
| `docker-compose.dev.yml` | hot-reload development runtime |
| `start-wenxian.command` / `stop-wenxian.command` | stable macOS startup wrappers |
| `start-wenxian-dev.command` / `stop-wenxian-dev.command` | dev-mode wrappers |
| `deploy/` | server-side update and persistence scripts |
| `scripts/export-api-runs.py` | export persisted runtime data |
| `scripts/repair-api-runs-paths.py` | rewrite older absolute paths after migration |
| `scripts/relativize-api-runs-paths.py` | convert older data into stored-relative format |

## Start Here When

- the stack will not boot locally
- Docker, env, or port behavior changed
- runtime data must be moved between machines or repaired after a path shift
- deployment flow documentation needs to match the actual scripts

## Typical Changes

- tweak compose files, env loading, or startup scripts
- add operator documentation to the root README
- update migration or path-repair helpers

## Watch-Outs

- this machine may not have local `node` or `npm`, so Docker remains the safer path for frontend validation here
- deployment docs should match the shipped scripts, not an idealized flow
- data migration changes often need a storage-path check too

## Common Verifications

- `docker compose -f /Users/mao/Documents/langchain/docker-compose.local.yml up -d --build`
- `curl http://127.0.0.1:8000/api/health`
- script compilation or dry-run checks when touching migration helpers
