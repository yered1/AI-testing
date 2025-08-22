# AI Testing Platform — Completeness v0.8.1

This drop restores the **full API surface** + **missing migrations** so UI v2, Findings/Reports, and the Agent Bus all work together.

## What’s in this overlay
- `orchestrator/app_v2.py` — full v0.8.1 (catalog, engagements, validate, plan, runs+SSE, controls, quotas, approvals, findings, artifacts, reports, agents, jobs, brain, listings)
- Alembic `0005_agents_jobs.py`, `0006_brain_autoplan.py`
- `orchestrator/pyproject.toml` — adds **jinja2** and **sse-starlette**
- `.env.example` — adds `OPA_URL`, `SIMULATE_PROGRESS`, `EVIDENCE_DIR`, `SLACK_WEBHOOK`
- `scripts/smoke_v081.sh` — end‑to‑end smoke

## Apply (macOS)
```bash
cd /path/to/AI-testing
git checkout -b completeness-v081
unzip -o ~/Downloads/ai-testing-completeness-v081.zip
git add -A
git commit -m "Completeness v0.8.1: full app_v2 + 0005/0006 + deps + env"
```

## Migrate & Run
```bash
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
# UI (optional)
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.ui.yml up --build -d ui
open http://localhost:3000
```

## Quick Smoke
```bash
bash scripts/smoke_v081.sh
```



# Delta v0.8.4 — Add routers (v2), Catalog, Dev Agent, Evidence (additive)

This drop adds:
- **v2 Routers**: quotas, approvals, findings, artifacts, reports, agents bus, brain (autoplan), listings — mounted automatically.
- **Catalog**: baseline tests + packs.
- **Dev Agent** that speaks the bus (`agents/dev_agent`) + compose extension.
- **Evidence** volume override (`infra/docker-compose.evidence.yml`).
- **.env** extras (`orchestrator/.env.append.example`).
- **Smoke** script `scripts/smoke_v084.sh`.

## Apply
```bash
git checkout -b overlay-v084
unzip -o ~/Downloads/ai-testing-overlay-v084.zip
git add -A
git commit -m "v0.8.4 overlay: v2 routers + catalog + dev agent + evidence"
```

## Run
```bash
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# (optional) persist evidence
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.evidence.yml up -d

# smoke
bash scripts/smoke_v084.sh
```



# Delta v0.9.0 — Extended Dev Agent + OPA v2 + Postman (additive)

Adds:
- **Dev Agent (extended)** with pluggable adapters (`echo`, `nmap_tcp_top_1000`) and dry‑run by default (`ALLOW_ACTIVE_SCAN=0`).
- **Agent compose**: `infra/docker-compose.agents.ext.yml`, Dockerfile installs `nmap`.
- **OPA policy v2**: `policies/policy.v2.rego` with risk + quota checks.
- **Postman collection**: `docs/postman/AI-testing.postman_collection.json`.
- **Scripts**: `scripts/agent_devext_up.sh`, `scripts/cleanup_evidence.sh`.

## Use

1) Build core + migrate
```bash
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
```

2) (Optional) Persist evidence
```bash
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.evidence.yml up -d
```

3) Create an agent token, then start the extended agent
```bash
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json' -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"devext"}' | jq -r .token)

AGENT_TOKEN="$TOKEN" bash scripts/agent_devext_up.sh
# To actually run nmap (be sure you're authorized), also set ALLOW_ACTIVE_SCAN=1
# ALLOW_ACTIVE_SCAN=1 AGENT_TOKEN="$TOKEN" bash scripts/agent_devext_up.sh
```

4) Postman: import `docs/postman/AI-testing.postman_collection.json`.

> **Safety**: By default the agent is **dry‑run** for active scans. Enable only when you have written permission for the target.



# Delta v0.9.1 — CI + Makefile + CI-friendly smoke (additive)

Adds:
- **GitHub Actions CI** workflow `.github/workflows/ci.yml` (docker-compose up, migrate, Python smoke against API).
- **Compose CI override** `infra/docker-compose.ci.yml` enabling `SIMULATE_PROGRESS=true` for predictable runs.
- **Makefile** with `up`, `down`, `migrate`, `logs`, `ui-up`, `smoke`, `agent-devext`, `clean`.
- **Python smoke** `scripts/ci_smoke.py` (no jq dependency).

## Local quickstart
```bash
make up
make migrate
python scripts/ci_smoke.py
```

## CI on GitHub
Push any branch and the workflow runs automatically. On failures, logs from `orchestrator`, `db`, and `opa` are printed.



# Delta v0.9.2 — OIDC/MFA proxy + PDF reporter (additive)

Adds:
- **Auth proxy stack** (`infra/docker-compose.auth.yml`) with **oauth2-proxy** + **Nginx** (`infra/auth/*`).
- **PDF Reporter** microservice (`infra/reporter.Dockerfile`, `services/reporter/app.py`) + compose override (`infra/docker-compose.reports.yml`).
- Scripts: `scripts/auth_stack_up.sh`, `scripts/render_pdf_from_api.sh`.
- Docs: `docs/AUTH_SETUP.md`, `docs/REPORTS_PDF.md`.

## Use (auth)
```bash
cp infra/auth/.env.auth.example infra/auth/.env.auth
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.auth.yml up -d reverse-proxy oauth2-proxy
open http://localhost:8081
```

## Use (PDF)
```bash
docker compose -f infra/docker-compose.reports.yml up --build -d reporter
bash scripts/render_pdf_from_api.sh <RUN_ID>
```

All additive — your current Orchestrator and routers remain untouched.



# Delta v0.9.3 — Web Active Agents (ZAP + Nuclei) & Pack (additive)

Adds:
- **ZAP web agent** (`agents/zap_agent`, `infra/agent.zap.Dockerfile`, `infra/docker-compose.agents.zap.yml`, `scripts/agent_zap_up.sh`).
- **Nuclei agent** (`agents/nuclei_agent`, `infra/agent.nuclei.Dockerfile`, `infra/docker-compose.agents.nuclei.yml`, `scripts/agent_nuclei_up.sh`).
- **Catalog** tests: `web_zap_baseline`, `web_nuclei_default` and pack `default_web_active`.
- **OPA v3** (`policies/policy.v3.rego`) with clearer gates for active adapters.
- **Smoke** `scripts/smoke_web_active_v093.sh`.

Usage:
```bash
# Start core
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# Get agent token
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json' -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"webagents"}' | jq -r .token)

# Start agents (ZAP baseline is non-intrusive; full mode requires ALLOW_ACTIVE_SCAN=1)
AGENT_TOKEN="$TOKEN" bash scripts/agent_zap_up.sh
AGENT_TOKEN="$TOKEN" bash scripts/agent_nuclei_up.sh

# Run a web engagement using the active pack
API=http://localhost:8080 TENANT=t_demo bash scripts/smoke_web_active_v093.sh
```



# Delta v0.9.4 — RBAC via OIDC Groups at Proxy + OPA v4 (additive)

Adds:
- **RBAC reverse proxy** with Nginx + oauth2-proxy using groups claim:
  - `infra/docker-compose.auth-rbac.yml`
  - `infra/auth/oauth2_proxy.rbac.cfg`, `infra/auth/nginx.rbac.conf`
  - `infra/auth/.env.auth.example` (extended with `OAUTH2_PROXY_OIDC_GROUPS_CLAIM`)
  - `scripts/auth_rbac_up.sh`
  - Docs: `docs/AUTH_RBAC_MAPPING.md`
- **OPA v4 policy** (`policies/policy.v4.rego`) reflecting roles & tenant isolation.

## Start (dev)
```bash
cp infra/auth/.env.auth.example infra/auth/.env.auth
# Fill ISSUER/CLIENT/SECRET/COOKIE_SECRET; ensure IdP emits 'groups'
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.auth-rbac.yml up -d reverse-proxy oauth2-proxy
open http://localhost:8081
```

## Groups → Tenant & Role
- Expected groups: `tenant_<id>`, and one or more of `role_admin|role_reviewer|role_user`.
- Nginx sets headers: `X-User`, `X-Email`, `X-Groups`, `X-Tenant-Id` (extracted from groups).

## Enforcement
- Proxy-level hard gates:
  - Admin-only: `/v2/quotas`, `/v1/engagements/{id}/plan`
  - Admin or reviewer: `/v2/approvals`
- OPA-level: use `policies/policy.v4.rego` to gate actions like `start_run`, `approve`, `view_report`, risk tiers, and intrusive runs.

> This overlay is additive and does not modify your backend. When ready, disable any dev header bypass in production and rely solely on the proxy headers.
