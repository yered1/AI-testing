# AI Pentest Platform

**Current status**: v2 orchestrator with Postgres + RLS, OPA policy checks, quotas & approvals, live progress (SSE), **and Findings & Reporting v1**.

## Quick start (v2)
```bash
cp orchestrator/.env.example orchestrator/.env
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
open http://localhost:8080/docs
```

### Dev mode auth
Use headers on requests: `X-Dev-User, X-Dev-Email, X-Tenant-Id`

## Key features (v2)
- **DB + RLS**: tenants, engagements, plans, runs
- **Catalog & packs**: `/v1/catalog`, `/v1/catalog/packs`
- **Validation & estimates**: `/v2/engagements/{id}/plan/validate`
- **Preview**: `/v2/engagements/{id}/plan/preview`
- **Quotas**: `/v2/quotas` + enforcement
- **Approvals**: `/v2/approvals` + gating for intrusive tests
- **Policy (OPA)**: deny if scope invalid or intrusive without approval
- **Live progress (SSE)**: `/v2/runs/{run_id}/events`, **run controls** (`pause|resume|abort`)
- **Findings & Reporting v1**: `POST/GET /v2/findings`, `GET /v2/reports/engagement/{id}?format=md|json`

See `README_BATCH5.md` for concrete API examples.
