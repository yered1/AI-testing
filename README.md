# AI Testing Platform — Batch 1 (Auth + DB + RLS-ready)

This batch upgrades the walking skeleton to a **database-backed**, **OIDC-ready**, **tenant-isolated** API.

## What’s new
- **FastAPI orchestrator** now uses **Postgres** via SQLAlchemy.
- **Alembic** migrations create core tables and **RLS policies** (scaffold).
- **OIDC-ready** auth dependency with **MFA claim check**; **DEV bypass** supported.
- **Tenant membership** and **per-request GUC** (`app.current_tenant`) to support RLS.
- OpenAPI security scheme and auth docs. 

> NOTE: RLS is enabled in migrations, but requires each request to set the tenant GUC. This build expects an `X-Tenant-Id` header (DEV) or derives tenant from membership (PROD).

## Quick start (Docker)
```bash
# env file (dev)
cp orchestrator/.env.example orchestrator/.env

# start services
docker compose -f infra/docker-compose.yml up --build

# open docs
open http://localhost:8080/docs
```

## Local dev (without Docker)
```bash
# Postgres running locally and DATABASE_URL set
cd orchestrator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app:app --reload --host 0.0.0.0 --port 8080
```

## Auth modes
- **DEV_BYPASS_AUTH=true** (default): use `X-Dev-User`, `X-Dev-Email`, and `X-Tenant-Id` headers to simulate auth.
- **OIDC**: set `OIDC_ISSUER`, `OIDC_AUDIENCE`. Token must include `amr` with `mfa` (if `REQUIRE_MFA=true`).

## Next batches
- Catalog Checkbox UI endpoints (dry-run/estimate), Quotas & Approvals, OPA enforcement, Live progress, Findings.
