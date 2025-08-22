# AI Testing Platform — Orchestrator + OPA + Agents + UI + Reporting

Multi-tenant, LLM-assisted pentest orchestrator with:
- **DB + RLS** (Postgres) tenant isolation
- **OIDC/MFA-ready auth** (DEV headers for local)
- **Catalog & Packs** with checkbox selection
- **Validation** (estimates + OPA policy gating) & **Plan preview**
- **Quotas & Approvals**
- **Run execution** with **SSE live events** + pause/resume/abort
- **Agents bus** (enroll tokens, registration, job leasing, progress)
- **Findings & Artifacts** + exportable **reports** (JSON/MD/HTML)
- **Brain** (Auto‑Plan suggestions; external LLM provider hook)
- **Web UI v2** to drive everything end-to-end

> Use only against assets you are authorized to test.

---

## Quick Start

```bash
# 1) Bring up stack
cp orchestrator/.env.example orchestrator/.env
docker compose -f infra/docker-compose.v2.yml up --build -d

# 2) Apply migrations (0001..0006)
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# 3) (Optional) UI
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.ui.yml up --build -d ui
open http://localhost:3000

# API docs
open http://localhost:8080/docs
```

**DEV headers** to include in calls (until OIDC is configured):
`X-Dev-User`, `X-Dev-Email`, `X-Tenant-Id`

---

## Workflow

1. **Create engagement** → `POST /v1/engagements`
2. **(Optional) Auto‑Plan** → `POST /v2/engagements/{id}/plan/auto`
3. **Validate** → `POST /v2/engagements/{id}/plan/validate`
4. **Create plan** → `POST /v1/engagements/{id}/plan`
5. **Start run** → `POST /v1/tests`
6. **Live events** → `GET /v2/runs/{run}/events` (SSE)
7. **Controls** → `POST /v2/runs/{run}/control` (`pause|resume|abort`)
8. **Findings** → `POST/GET /v2/runs/{run}/findings`
9. **Artifacts** → `POST /v2/runs/{run}/artifacts`
10. **Reports** → `GET /v2/reports/run/{run}.{json|md|html}`

---

## Agents

- **Create token** → `POST /v2/agent_tokens`  
- **Agent registers** → `POST /v2/agents/register` → returns `agent_id` + `agent_key`  
- **Heartbeat** → `POST /v2/agents/heartbeat`  
- **Lease next job** → `POST /v2/agents/lease`  
- **Progress** → `POST /v2/jobs/{job}/events`  
- **Complete** → `POST /v2/jobs/{job}/complete`

### Dev agent

```bash
# Create token
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"dev1"}' | jq -r .token)

# Start the agent container
AGENT_TOKEN=$TOKEN docker compose   -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.yml   up --build -d agent_dev1
```

---

## Quotas & Approvals

- **Set quota** → `POST /v2/quotas`  
- **Get quota** → `GET /v2/quotas/{tenant_id}`  
- **Request approval** → `POST /v2/approvals`  
- **Decide** → `POST /v2/approvals/{id}/decide`  
- *(If your build includes Batch 10 API additions)* **List approvals** → `GET /v2/approvals?engagement_id=...`

---

## Brain (Auto‑Plan & Provider)

- **Suggest** → `POST /v2/engagements/{id}/plan/auto`  
- **Feedback** → `POST /v2/brain/feedback`  
- **Providers** → `GET /v2/brain/providers`

**External LLM provider (optional):**
- `LLM_HTTP_ENDPOINT`, `LLM_HTTP_TOKEN` (returns `{ tests: [ids], explanation: "..." }`)

---

## UI v2 Highlights

- Dev headers editor
- Engagement creation
- **Auto‑Plan** button (brain + packs)
- Validate/estimate and create plan
- Start run + Live SSE + controls
- Quotas & Approvals panel
- Agents panel (create token; list agents*)  
- Recent Runs list* → click to attach to SSE
- Findings actions + Report downloads

> *Panels marked with * use optional API listings. UI degrades gracefully if endpoints are missing.

---

## Config (env)

- **Auth**: `DEV_BYPASS_AUTH`, `REQUIRE_MFA`, `OIDC_ISSUER`, `OIDC_AUDIENCE`  
- **OPA**: `OPA_URL`  
- **Runtime**: `SIMULATE_PROGRESS`, `SLACK_WEBHOOK`, `EVIDENCE_DIR`  
- **UI**: `VITE_API_BASE`

---

## Troubleshooting

- **Migrations**: `docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head`  
- **CORS/UI**: ensure `VITE_API_BASE` is the API origin.  
- **OPA denies**: adjust `policies/policy.rego` or approve the request.  
- **Agents idle**: create a plan/run; check `agent_dev1` logs.

---

## Make targets

`make up | down | migrate | logs | ui-up | ui-down | smoke | reset-db | openapi`

---

## Roadmap

- Agent sandbox adapters (nmap, nuclei, ZAP) with safe defaults
- Remote bootstrap (edge site images) with secure tunnels
- PDF export pipeline
- Schedules/maintenance windows
- Audit trail + Prometheus metrics
