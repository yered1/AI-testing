# Reconciliation Pack — Orchestrator v0.8.0 (complete)

This overlay restores **complete** endpoints and **missing migrations** (0004–0006) to match the UI and docs.

## Apply (macOS)

```bash
cd /path/to/AI-testing
git checkout -b reconcile-v080
unzip -o ~/Downloads/ai-testing-reconcile-v080.zip
git add -A
git commit -m "Reconcile: full app_v2.py v0.8.0 + migrations 0004..0006 + dev agent compose"
```

## Migrate

```bash
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
```

## (Optional) Start a dev agent

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type': 'application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"dev1"}' | jq -r .token)

AGENT_TOKEN=$TOKEN docker compose   -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.yml   up --build -d agent_dev1
```

> If your compose lacks an evidence volume, artifacts store inside the orchestrator container. To persist, map a local folder to `/data/evidence` and set `EVIDENCE_DIR=/data/evidence` for the orchestrator.

## Confirm

- `GET /health` → version `0.8.0`
- `/v1/catalog`, `/v1/catalog/packs`
- Engagement → validate → plan → **/v1/tests**
- SSE: `/v2/runs/{id}/events`
- Controls: `/v2/runs/{id}/control`
- Quotas: `/v2/quotas` (POST/GET)
- Approvals: `/v2/approvals` (POST/decide/GET list)
- Findings & Artifacts
- Reports: `/v2/reports/run/{id}.{json|md|html}`
- Agents bus: tokens, register, heartbeat, lease, events, complete
- Brain: `/v2/engagements/{id}/plan/auto`, `/v2/brain/feedback`, `/v2/brain/providers`
- Listings: `/v2/runs/recent`, `/v2/agents`
