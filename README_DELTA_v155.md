# Delta v1.5.5 — CI Alembic fix (import path) + OPA/DB overrides + Kali tools extras

## CI changes
- Migrations now run with `PYTHONPATH=/app` and `workdir=/app/orchestrator` so `import orchestrator` resolves.
- Compose overrides included in **every** CI command:
  - `infra/docker-compose.opa.compat.yml` (valid OPA tag; loads only `policies_enabled/`)
  - `infra/docker-compose.db.ci.yml` (DB creds + DSN to orchestrator)
  - `infra/docker-compose.health.yml` (DB healthcheck)

Use `.github/workflows/ci_v5.yml` or patch your existing `ci.yml` with `scripts/ci_patch_v155.sh`.

## Local mirror
- `scripts/ci_local_up_v155.sh` runs build → migrate → API → smoke locally.

## Kali OS agent
- Added `gobuster`, `ffuf` (POST/JSON), `sqlmap` extras. Merge with:
```
bash scripts/merge_kali_tools_v155.sh
```
All active scans still require `ALLOW_ACTIVE_SCAN=1` and your OPA/approvals/quotas stay in force.
