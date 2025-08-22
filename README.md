# AI Testing Platform — v0.8.0 (Complete Orchestrator + UI + Agents)

Multi-tenant, LLM-assisted pentest orchestrator with:
- **Postgres + RLS** tenant isolation
- **OIDC-ready Auth** (DEV headers for local)
- **Catalog & Packs** (checkbox selection)
- **Validation** (estimates + **OPA** policy) & **Plan**
- **Quotas & Approvals**
- **Run Execution** with **SSE live events** + controls
- **Agents Bus** (enroll, register, lease, progress)
- **Findings & Artifacts** + **Reports** (JSON/MD/HTML)
- **Brain** (Auto‑Plan + Feedback)
- **UI v2** driving the flow end-to-end

> Use only against assets you are authorized to test.

---

## Quick Start

```bash
cp orchestrator/.env.example orchestrator/.env
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
# UI (optional)
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.ui.yml up --build -d ui
open http://localhost:8080/docs
open http://localhost:3000
```

**DEV headers** (until OIDC/MFA is wired): `X-Dev-User`, `X-Dev-Email`, `X-Tenant-Id`

---

## Workflow

1) **Create engagement** → `POST /v1/engagements`  
2) **Auto‑Plan** → `POST /v2/engagements/{id}/plan/auto`  
3) **Validate** → `POST /v2/engagements/{id}/plan/validate`  
4) **Create plan** → `POST /v1/engagements/{id}/plan`  
5) **Start run** → `POST /v1/tests`  
6) **Live events** → `GET /v2/runs/{run}/events` (SSE)  
7) **Controls** → `POST /v2/runs/{run}/control` (`pause|resume|abort`)  
8) **Findings** → `POST/GET /v2/runs/{run}/findings`  
9) **Artifacts** → `POST /v2/runs/{run}/artifacts`  
10) **Reports** → `GET /v2/reports/run/{run}.{json|md|html}`

---

## Quotas & Approvals

- `POST /v2/quotas` → `{ tenant_id, monthly_budget, per_plan_cap }`  
- `GET /v2/quotas/{tenant_id}`  
- `POST /v2/approvals` → create request  
- `POST /v2/approvals/{id}/decide` → approve/deny  
- `GET /v2/approvals?engagement_id=...`

---

## Agents

- `POST /v2/agent_tokens` → enrollment token  
- `POST /v2/agents/register` → `{ agent_id, agent_key }`  
- `POST /v2/agents/heartbeat`  
- `POST /v2/agents/lease` → returns next job  
- `POST /v2/jobs/{job}/events`  
- `POST /v2/jobs/{job}/complete`

**Dev agent**:

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"dev1"}' | jq -r .token)

AGENT_TOKEN=$TOKEN docker compose   -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.yml   up --build -d agent_dev1
```

---

## Brain

- `POST /v2/engagements/{id}/plan/auto` → heuristic + packs  
- `POST /v2/brain/feedback`  
- `GET /v2/brain/providers`

To plug an external LLM provider, add: `LLM_HTTP_ENDPOINT`, `LLM_HTTP_TOKEN` and wire a tiny proxy (not included in this pack).

---

## Configuration

`.env` keys you may set:
- `OPA_URL` (default points to the `opa` service)  
- `SIMULATE_PROGRESS=true`  
- `EVIDENCE_DIR=/data/evidence`  
- `SLACK_WEBHOOK=`

---

## Troubleshooting

- Migrations: `docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head`  
- CORS/UI: ensure `VITE_API_BASE` matches your API origin.  
- OPA denies: edit `policies/policy.rego` or approve requests.  
- Agents idle: ensure a run exists; check agent logs.  
- Evidence: map a host volume for `/data/evidence` to persist artifacts.

---

## Make (optional)

`make up | down | migrate | logs | ui-up | ui-down | smoke | reset-db | openapi`

---

## Roadmap

- Agent adapters (nmap, nuclei, ZAP) with safe defaults  
- Remote bootstrap (edge images + secure tunnel)  
- PDF pipeline, schedules, metrics, audit trail
