# v1.5.4 — CI Alembic import fix + OPA/DB overrides + Kali tools extras (additive)

## CI
- **Migrate before API** with PATH fixes for Alembic import:
  - `scripts/ci_migrate_v154.sh` -> sets `PYTHONPATH=/app` and runs `alembic -c orchestrator/alembic.ini upgrade head` with `-w /app`.
- OPA compat: `infra/docker-compose.opa.compat.yml` forces a valid tag and mounts `policies_enabled/` only.
- DB CI env: `infra/docker-compose.db.ci.yml` sets `postgres/postgres` and DB `aitest` and injects DSNs into orchestrator.
- Health gate: `infra/docker-compose.health.yml` adds `pg_isready` healthcheck.
- New workflow: `.github/workflows/ci_v4.yml` (or use `scripts/ci_patch_v154.sh` to modify existing).

## Features
- **Kali OS agent** tool extras: `naabu` + `masscan` safe templates. Merge with:
  ```bash
  bash scripts/merge_kali_tools_v154.sh
  ```

## Local CI mirror
```bash
bash scripts/ci_local_up_v154.sh
python scripts/ci_smoke.py
```
