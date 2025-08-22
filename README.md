# AI Pentest Platform

**Status:** v2 orchestrator with Postgres + RLS, OPA policy checks, quotas & approvals, live progress (SSE), run controls, and **Findings & Reporting v1**.  
The original v1 in-memory skeleton remains for reference.

## Quick start (v2)

```bash
cp orchestrator/.env.example orchestrator/.env
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
open http://localhost:8080/docs
```

### Dev mode auth
Use headers on requests:
```
X-Dev-User, X-Dev-Email, X-Tenant-Id
```
Set `REQUIRE_MFA=true` and OIDC vars later to enable real auth.

## Features (v2)

- **DB + RLS**: tenants, users, memberships, engagements, plans, runs
- **Catalog & packs**: `/v1/catalog`, `/v1/catalog/packs`
- **Validation & estimates**: `/v2/engagements/{id}/plan/validate`
- **Preview**: `/v2/engagements/{id}/plan/preview`
- **Quotas & Approvals**: `/v2/quotas`, `/v2/approvals` + enforcement
- **Policy (OPA)**: deny if scope invalid or intrusive without approval
- **Live progress (SSE)**: `/v2/runs/{run_id}/events`
- **Run controls**: `/v2/runs/{run_id}/control` (`pause|resume|abort`)
- **Optional Slack notifications**: set `SLACK_WEBHOOK`
- **Findings & Reporting v1**:
  - Ingest: `POST /v2/runs/{run_id}/findings:ingest`
  - List: `/v2/runs/{run_id}/findings`, `/v2/engagements/{id}/findings`
  - Detail: `/v2/findings/{finding_id}`
  - State: `POST /v2/findings/{id}/state` (open|accepted|resolved|false_positive)
  - Reports: `/v2/reports/{run_id}.json`, `/v2/reports/{run_id}.md`
  - Evidence store under `ARTIFACT_DIR` (default `/app/data/artifacts`)

## Typical flow

1. **Create engagement** → `POST /v1/engagements`
2. **(Optional) Set quotas** → `POST /v2/quotas`
3. **Validate/Preview** → `/v2/engagements/{id}/plan/validate|preview`
4. **Create plan** → `POST /v1/engagements/{id}/plan`
5. **Start test** → `POST /v1/tests`
6. **Watch live events** → `GET /v2/runs/{run_id}/events` (SSE)
7. **Pause/Resume/Abort** → `POST /v2/runs/{run_id}/control`
8. **Ingest findings** → `POST /v2/runs/{run_id}/findings:ingest`
9. **Export reports** → `/v2/reports/{run_id}.json` or `.md`

## Notes
- OPA runs as a sidecar via `infra/docker-compose.v2.yml`.
- `SIMULATE_PROGRESS=true` generates demo events; wire real agents later.
- Use only against assets with written authorization.
