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



# Delta v0.9.5 — Agent Artifacts + Lease2 (additive)

Adds:
- **/v2/agents/lease2**: extended lease API (returns run_id, plan_id, engagement_id).
- **/v2/jobs/{job_id}/artifacts**: agent-authenticated artifact upload (stored under EVIDENCE_DIR).
- **v2 agents** for ZAP and Nuclei that support `lease2` and auto-upload generated artifacts.
- **Smoke**: `scripts/smoke_artifacts_v095.sh` to verify end-to-end uploads.

Apply:
```bash
git checkout -b overlay-v095
unzip -o ~/Downloads/ai-testing-overlay-v095.zip
git add -A && git commit -m "v0.9.5 overlay: lease2 + agent artifact upload + v2 agents"
bash scripts/enable_routers_v095.sh   # one-time: append router includes
```

Run:
```bash
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# (optional) persist evidence
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.evidence.yml up -d

# token + agents
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json' -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"zapv2"}' | jq -r .token)
AGENT_TOKEN="$TOKEN" bash scripts/agent_zap_v2_up.sh

# smoke
API=http://localhost:8080 TENANT=t_demo bash scripts/smoke_artifacts_v095.sh
```

Notes:
- ZAP v2 agent uploads `zap_report.html` and `zap_report.json` as artifacts if present.
- Nuclei v2 agent uploads `nuclei.jsonl` artifact if produced.
- Agents first try `lease2`; if unavailable, they fall back to the original `lease` (uploads then skipped due to missing job->run mapping).



# Delta v0.9.6 — Report Bundle ZIP + Artifacts Index (additive)

Adds:
- **/v2/reports/run/{run_id}.zip** — one-click export: `report.md`, `report.html`, `report.json` + `artifacts/*` files
- **/v2/runs/{run_id}/artifacts/index.json** — machine-readable artifact list
- Router auto-mount script: `scripts/enable_reports_bundle_v096.sh`
- Smoke: `scripts/smoke_bundle_v096.sh`

## Apply
```bash
unzip -o ~/Downloads/ai-testing-overlay-v096.zip
git add -A && git commit -m "v0.9.6 overlay: report bundle zip + artifacts index"
bash scripts/enable_reports_bundle_v096.sh
```

## Use
```bash
# Download a zip bundle for a run
curl -L http://localhost:8080/v2/reports/run/<RUN_ID>.zip \\
  -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo' \\
  -o run_<RUN_ID>_bundle.zip
```

> The bundle reads files from `EVIDENCE_DIR` and includes only files present on disk and recorded in DB.



# Delta v0.9.7 — Minimal UI (additive)

Adds a lightweight UI served by the orchestrator:
- Routes: `/ui`, `/ui/new`, `/ui/runs/{run_id}`, `/ui/admin`
- Static assets at `/ui/static/*` (JS+CSS)
- Uses existing API endpoints (catalog, plan/validate, create plan, start run, SSE events, artifacts, reports, bundle)
- No overwrites; mounted via `bootstrap_extras.py`

## Apply
```bash
git checkout -b overlay-v097
unzip -o ~/Downloads/ai-testing-overlay-v097.zip
git add -A && git commit -m "v0.9.7 overlay: minimal UI (additive)"
bash scripts/enable_ui_v097.sh   # mounts the UI router
```

## Run
```bash
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
open http://localhost:8080/ui
# or, if using OIDC/MFA proxy: http://localhost:8081/ui
```



# Delta v0.9.8 — Code Review (Semgrep) + Artifact Downloads + UI page (additive)

Adds:
- **Semgrep agent** (`agents/semgrep_agent`, `infra/agent.semgrep.Dockerfile`, `infra/docker-compose.agents.semgrep.yml`, `scripts/agent_semgrep_up.sh`).
- **Catalog**: `code_semgrep_default` test + pack `default_code_review`.
- **Artifact download endpoint**: `GET /v2/artifacts/{artifact_id}/download` (agent or user auth).
- **UI Code Review page**: `/ui/code` with create→plan→run→upload flow.
- **Enable script**: `scripts/enable_code_review_v098.sh` to mount routers.
- **Smoke**: `scripts/smoke_code_review_v098.sh`.

Quickstart:
```bash
# Core up & migrate
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# Mount routers
bash scripts/enable_code_review_v098.sh

# Agent token + start
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json' -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"semgrep1"}' | jq -r .token)
AGENT_TOKEN="$TOKEN" bash scripts/agent_semgrep_up.sh

# Try UI
open http://localhost:8080/ui/code  # or http://localhost:8081/ui/code behind OIDC proxy

# CLI smoke
API=http://localhost:8080 TENANT=t_demo bash scripts/smoke_code_review_v098.sh
```




# Delta v0.9.9 — Mobile APK Static Analysis (Androguard) + UI page (additive)

Adds:
- **Mobile APK agent** (`agents/mobile_apk_agent`) with lease2 support, downloads APK from run artifacts, analyzes with **androguard**, uploads `apk_summary.json` and (best effort) `AndroidManifest.xml`.
- **Agent container/compose**: `infra/agent.mobile_apk.Dockerfile`, `infra/docker-compose.agents.mobile_apk.yml`, `scripts/agent_mobile_apk_up.sh`.
- **Catalog**: test `mobile_apk_static_default` and pack `default_mobile_static`.
- **UI**: `/ui/mobile` to guide APK upload → auto plan → run → results.
- **Smoke**: `scripts/smoke_mobile_v099.sh` (set `APK=/path/to/app.apk`).

## Use

```bash
# Apply overlay
unzip -o ai-testing-overlay-v099.zip
bash scripts/enable_mobile_v099.sh

# Start core
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# Start agent (after creating a token)
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens  -H 'Content-Type: application/json' -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'  -d '{"tenant_id":"t_demo","name":"mobile_apk"}' | jq -r .token)
AGENT_TOKEN="$TOKEN" bash scripts/agent_mobile_apk_up.sh

# UI
open http://localhost:8080/ui/mobile
```

> Notes: The analysis is **static** and safe. Provide an APK via the UI or `POST /v2/runs/{id}/artifacts` with label `mobile_apk`. The agent prefers `/v2/agents/lease2` to discover the run context; falls back to legacy lease if needed.
-e 



# Delta v1.0.0 — Test Builder UI (additive)

Adds a self-serve UI at **/ui/builder** to:
- Create an engagement (tenant, type, scope)
- Browse **catalog** (tests + packs), select via checkboxes
- Optional **per-test params** editor (JSON per test)
- **Validate** → **Create Plan** → **Start Run**
- Quick links to live events, findings, artifacts, and the **Report Bundle** (.zip)

## Apply
```bash
git checkout -b overlay-v100
unzip -o ~/Downloads/ai-testing-overlay-v100.zip
git add -A && git commit -m "v1.0.0 overlay: Test Builder UI (additive)"
bash scripts/enable_ui_builder_v100.sh
bash scripts/merge_readme_v100.sh
```

## Use
Open **http://localhost:8080/ui/builder** (or **:8081** when behind OIDC proxy).



# Delta v1.1.0 — Enhanced Reports (HTML/MD/PDF) with Taxonomy & CVSS (additive)

Adds:
- **Enhanced report endpoints**: `/v2/reports/enhanced/run/{id}.{html|md|pdf}`
- **Taxonomy/CVSS**: OWASP Top 10 (2021) mapping, keyword heuristics to tag findings, and CVSS v3.1 base score from vector (if provided).
- **Templates**: `orchestrator/report_templates/*`
- **Enable**: `scripts/enable_reports_enhanced_v110.sh`
- **Smoke**: `scripts/smoke_reports_enhanced_v110.sh`

## Use
```bash
# Enable router
bash scripts/enable_reports_enhanced_v110.sh

# Start core & migrate
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# (optional) start reporter & set REPORTER_URL
docker compose -f infra/docker-compose.reports.yml up --build -d reporter
# add to orchestrator env: REPORTER_URL=http://reporter:8080  (compose override or env)
# then restart orchestrator

# Smoke
API=http://localhost:8080 TENANT=t_demo bash scripts/smoke_reports_enhanced_v110.sh
```



# Delta v1.2.0 — Brain v3 (LLM‑ready) + Web Discovery Agent (dnsx/httpx) (additive)

Adds:
- **Brain v3** with pluggable providers (heuristic default; OpenAI/Azure/Anthropic optional), and endpoints:
  - `GET /v3/brain/providers`
  - `POST /v3/brain/plan` and `POST /v3/brain/enrich`
  - `POST /v3/brain/learn` (feedback)
- **DB**: `brain_traces` table with RLS (migration `0007`).
- **Discovery Agent** (`web_discovery`): dnsx + httpx; uploads artifacts (`dnsx.txt`, `httpx.jsonl`).
- **Catalog**: tests `network_dnsx_resolve`, `web_httpx_probe`; packs `default_web_discovery`, `default_external_min`.
- **Compose & Scripts**: agent Dockerfile/compose + `agent_web_discovery_up.sh` and smokes.

## Apply
```bash
git checkout -b overlay-v120
unzip -o ~/Downloads/ai-testing-overlay-v120.zip
git add -A
git commit -m "v1.2.0 overlay: brain v3 + discovery agent + catalog (additive)"

# mount router
bash scripts/enable_brain_v3_v120.sh
```

## Run
```bash
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
```

## Try Brain v3 + Discovery
```bash
# start discovery agent
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json' -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"discover"}' | jq -r .token)
AGENT_TOKEN="$TOKEN" bash scripts/agent_web_discovery_up.sh

# smoke
API=http://localhost:8080 TENANT=t_demo bash scripts/smoke_brain_v120.sh
```

## Configure optional LLM providers
Set env vars and restart orchestrator:
- **OpenAI**: `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-4o-mini`, `OPENAI_BASE_URL=https://api.openai.com/v1`
- **Anthropic**: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL=claude-3-5-sonnet-20240620`
- **Azure OpenAI**: `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`

If not configured, the planner uses the **heuristic** provider.



# Delta v1.3.0 — Brain v3 providers + guarded planning; Internal network & ZAP auth agents (additive)

Adds:
- **Brain providers & engine**: heuristic (default), OpenAI, Anthropic, Azure OpenAI; file-based cache; risk tier inference.
- **Guarded planning API**: `/v3/brain/plan/guarded` (flags `approval_required` when intrusive).
- **Templates** for planning guidance (web/network/code/mobile).
- **Agents**: internal **network** (nmap full/udp top 200), **ZAP auth** (dry-run by default; requires ALLOW_ACTIVE_SCAN=1).
- **Catalog**: `network_nmap_tcp_full`, `network_nmap_udp_top_200`, `web_zap_auth_full`; pack `default_internal_network`.
- **UI**: `/ui/brain` page to try Brain planning interactively.
- **Smokes**: `smoke_brain_guarded_v130.sh`, `smoke_internal_net_v130.sh`.

Quick start:
```bash
# Core + migrate
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# Mount routers/UI
bash scripts/enable_brain_plus_v130.sh

# Discovery agent (optional, complements planning)
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"discover"}' | jq -r .token)
AGENT_TOKEN="$TOKEN" bash scripts/agent_web_discovery_up.sh

# Network agent (intrusive; enable only with authorization)
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"net"}' | jq -r .token)
ALLOW_ACTIVE_SCAN=1 AGENT_TOKEN="$TOKEN" bash scripts/agent_network_up.sh

# ZAP auth agent (intrusive; requires creds and ALLOW_ACTIVE_SCAN=1)
AGENT_TOKEN="$TOKEN" ALLOW_ACTIVE_SCAN=1 bash scripts/agent_zap_auth_up.sh
```

Providers:
- OpenAI: set `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL` (optional).
- Anthropic: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`.
- Azure OpenAI: `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`.

Use `/ui/brain` to experiment with planning then finalize via the **Builder** page.




# Delta v1.4.0 — Repo Doctor + Safe Cleanup + Agent SDK + **Kali Remote Agent** (additive)

This drop focuses on **completeness & cleanup** and your key feature: a **remote agent that controls an OS with offsec tools** (Kali). No features removed.

## What's included
- **Repo Doctor** (`scripts/repo_doctor.py`, `scripts/run_repo_doctor.sh`)  
  Audit includes/routers/endpoints/agents. Produces a consolidation plan and lists *only safe junk* (pyc, __pycache__, .pytest_cache, .DS_Store).
- **Safe Cleanup** (`scripts/cleanup_safe.sh`)  
  Deletes *only* cache/temp files. No source/features touched.
- **Agent SDK** (`orchestrator/agent_sdk/`)  
  Shared HTTP client for agents (register, heartbeat, lease/lease2, events, complete, artifact upload).
- **Kali Remote Agent** (`agents/kali_remote_agent`)  
  SSH into a remote Kali box and run allowed tools (allowlist in `tools.yaml`). Uploads results via the existing artifact pipeline.
  - Dockerfile: `infra/agent.kali.remote.Dockerfile`
  - Compose: `infra/docker-compose.agents.kali.remote.yml`
  - Runner: `scripts/agent_kali_remote_up.sh`

## Usage

### Safe cleanup (optional)
```bash
bash scripts/cleanup_safe.sh
# or dry-run audit
bash scripts/run_repo_doctor.sh
```

### Start the Kali remote agent
Create a token:
```bash
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"kali-remote"}' | jq -r .token)
```

Set SSH details (use base64 key or password; key preferred):
```bash
export AGENT_TOKEN="$TOKEN"
export SSH_HOST=YOUR.KALI.IP
export SSH_USER=kali
export SSH_KEY_BASE64=$(base64 -w0 ~/.ssh/id_rsa)   # or set SSH_PASSWORD
bash scripts/agent_kali_remote_up.sh
```

### Using the agent
Submit jobs via your planner/Builder using adapters:
- `run_tool` with params `{"name":"nmap_tcp_top_1000","args":"-vv 192.0.2.10"}` (see `agents/kali_remote_agent/tools.yaml`)
- `nmap_tcp_top_1000` with `{"target":"192.0.2.10"}` (honors `ALLOW_ACTIVE_SCAN`)

Artifacts (stdout/logs) are uploaded to the run’s evidence via `/v2/jobs/{job_id}/artifacts`.

> **Safety**: Active scanning only runs when `ALLOW_ACTIVE_SCAN=1`. Keep the tool allowlist tight in `tools.yaml`.




# Delta v1.4.2 — Kali OS Agent (HTTPS pull) + Safer Cleanup (additive)

**Highlights**
- **Kali OS Agent** that runs natively on Kali, connects to the orchestrator via the existing **HTTPS agent bus** (v2) and executes **allowlisted** offsec tools locally. Uploads artifacts and posts results back.
- **Catalog** tests & pack targeting `kali_os` agent kind.
- **Cleanup tools:** stronger but **safe** cache/junk cleanup (dry-run by default), repo doctor report, stricter `.gitignore` merging.

## Install the Kali OS Agent (on your Kali box)
```bash
# From your repo root on the Kali host (or copy the files over):
# 1) Create a token
TOKEN=$(curl -s -X POST http://ORCH_HOST:8080/v2/agent_tokens \
  -H 'Content-Type: application/json' \
  -H 'X-Dev-User: dev' -H 'X-Dev-Email: dev@example.com' -H 'X-Tenant-Id: t_demo' \
  -d '{"tenant_id":"t_demo","name":"kali-os"}' | jq -r .token)

# 2) Install the agent as a systemd service
ORCH_URL=http://ORCH_HOST:8080 TENANT_ID=t_demo AGENT_TOKEN="$TOKEN" \
bash scripts/install_kali_os_agent.sh

# 3) Tail logs
sudo journalctl -u kali-os-agent -f
```

**Active scans** are **dry-run** by default. Explicitly allow:
```bash
sudo sed -i 's/ALLOW_ACTIVE_SCAN=0/ALLOW_ACTIVE_SCAN=1/' /etc/kali-os-agent/config.env
sudo systemctl restart kali-os-agent
```

**Allowlist tools** in `/etc/kali-os-agent/tools.yaml` (seeded with `nmap_tcp_top_1000`, `ffuf_dirb`, `gobuster_dir`, `sqlmap_basic`).

## Using the remote Kali tests
Use the **Test Builder** or curl to select the new tests / pack:
- Tests: `remote_kali_nmap_tcp_top_1000`, `remote_kali_run_tool`
- Pack: `default_remote_kali_min`

The orchestrator will create jobs targeted to `kali_os` agents; your agent polls `/v2/agents/lease`, runs the command, uploads artifacts, and completes the job.

## Cleanup & repo hygiene
```bash
# Inspect junk & large files
bash scripts/run_repo_doctor_v142.sh

# Safe cleanup (dry-run by default). Apply deletions with DRY_RUN=0
bash scripts/cleanup_strict_v142.sh
DRY_RUN=0 bash scripts/cleanup_strict_v142.sh

# Strengthen .gitignore
bash scripts/merge_gitignore_v142.sh
```

> These scripts **do not** remove any product features. They only remove caches and platform cruft. Docs/merge scripts remain unless you archive them manually.




# Delta v1.5.0 — Consolidation & Cleanup (safe) + Canonical router includes

This release focuses on consolidation without removing features:
- **README consolidation**: appends any `README_DELTA_v*.md` missing from `README.md`, then deletes delta files and old merge scripts.
- **Bootstrap repair**: rewrites `orchestrator/bootstrap_extras.py` to include **all** routers found under `orchestrator/routers`, and mounts UI static where available.
- **Strict cleanup**: removes platform junk and caches (`__MACOSX`, `.DS_Store`, `__pycache__`, etc.) with backup + DRY_RUN by default.
- **.gitignore**: strengthens to prevent junk from returning.

## Usage
```bash
# Consolidate README deltas, then delete delta/merge files
bash scripts/consolidate_readme_v150.sh

# Repair router includes (idempotent)
bash scripts/repair_bootstrap_extras_v150.sh
python3 scripts/verify_bootstrap_v150.py

# Clean junk (dry-run -> delete)
bash scripts/cleanup_strict_v150.sh
DRY_RUN=0 bash scripts/cleanup_strict_v150.sh

# Merge gitignore additions
bash scripts/merge_gitignore_v150.sh
```
