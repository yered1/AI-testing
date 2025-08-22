# AI Testing Platform — Orchestrator + OPA + UI + Reporting

A multi-tenant, LLM-assisted penetration-testing orchestrator with:
- **DB + RLS (Postgres)** for strict tenant isolation
- **OIDC/MFA-ready auth** (DEV headers by default)
- **Catalog & Packs** with **checkbox-style** selection
- **Dry-run validation** + **estimates** + **plan preview**
- **OPA policy** gating scope & intrusive actions
- **Quotas & Approvals** (monthly/per-plan caps; human approval for intrusive steps)
- **Run execution** with **live progress (SSE)** and **pause/resume/abort**
- **Findings ingestion**, **artifacts/evidence uploads**, and **exportable reports** (JSON/Markdown/HTML)
- **Optional Web UI** (React + Vite) to drive the entire flow

> Use this only against assets you are legally authorized to test.

---

## 1) Prerequisites

- macOS, Linux, or WSL2
- Docker Desktop 4.x+ (with Compose v2)
- `curl`, `jq`
- Optional for local dev: Python 3.11, Node 20 (if running UI locally outside Docker)

---

## 2) Repository Layout

```
AI-testing/
├─ orchestrator/                 # FastAPI app (v2)
│  ├─ app_v2.py                  # API 0.5.0 (SSE, quotas, approvals, findings, reports)
│  ├─ models.py, db.py, auth.py, tenancy.py, settings.py
│  ├─ templates/                 # report_run.{md,html}.j2
│  ├─ alembic/versions/          # 0001..0004 migrations
│  ├─ requirements-extra.txt
│  └─ .env.example
├─ catalog/                      # test items + packs
├─ policies/                     # OPA policy.rego
├─ infra/
│  ├─ docker-compose.v2.yml      # Orchestrator + Postgres + OPA (+ evidence volume)
│  ├─ orchestrator.Dockerfile.v2
│  ├─ docker-compose.ui.yml      # (If UI installed) React app served on :3000
│  └─ ui.Dockerfile              # (If UI installed)
├─ ui/                           # (If UI applied) Minimal React app
├─ scripts/                      # Utilities (smoke, reset DB, seed demo)
└─ postman/AI-Testing.postman_collection.json
```

---

## 3) Quick Start (Docker)

```bash
# 0) Set up env (dev mode)
cp orchestrator/.env.example orchestrator/.env

# 1) Bring up DB + OPA + Orchestrator (v2)
docker compose -f infra/docker-compose.v2.yml up --build -d

# 2) Apply DB migrations (0001..0004)
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# 3) API docs
open http://localhost:8080/docs
```

> **DEV Mode Auth**: supply headers on every call  
> `X-Dev-User: <you>` · `X-Dev-Email: <you@domain>` · `X-Tenant-Id: <tenant>`

To enable **real OIDC/MFA** later, see **Configuration** below.

---

## 4) Optional Web UI

If you applied the UI overlay (Batch 6), run:

```bash
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.ui.yml up --build -d ui
open http://localhost:3000
```

The UI lets you:
- Edit DEV headers
- Create Engagement → pick **packs/tests** → validate/preview → **create plan**
- **Start run**, watch **live events**, **pause/resume/abort**
- Upload **artifacts** and export **reports**

---

## 5) Configuration (env vars)

Edit `orchestrator/.env` or set environment in Compose.

**Core**
- `DATABASE_URL` — `postgresql+psycopg://app:app@db:5432/ai_testing`
- `LOG_LEVEL` — default `INFO`

**Auth**
- `DEV_BYPASS_AUTH` — `true` for DEV headers mode
- `REQUIRE_MFA` — `false` by default; set `true` to require `amr` contains `mfa|otp`
- `OIDC_ISSUER`, `OIDC_AUDIENCE` — OIDC verification (when `DEV_BYPASS_AUTH=false`)

**Policy / Safety**
- `OPA_URL` — default `http://opa:8181/v1/data/pentest/policy`

**Runtime / UX**
- `SIMULATE_PROGRESS` — `true` to generate demo step events
- `SLACK_WEBHOOK` — webhook for run started/completed/aborted messages
- `EVIDENCE_DIR` — default `/data/evidence` (Docker **volume** `evidence_data`)

**UI (if installed)**
- `VITE_API_BASE` — default `http://host.docker.internal:8080` in `docker-compose.ui.yml`

---

## 6) Typical Workflow (API)

1. **Create engagement** → `POST /v1/engagements`
2. **(Optional) Set tenant quota** → `POST /v2/quotas`
3. **Validate / Estimate** → `POST /v2/engagements/{id}/plan/validate`
4. **Preview** (optional) → `POST /v2/engagements/{id}/plan/preview`
5. **Create plan** → `POST /v1/engagements/{id}/plan`
6. **Start run** → `POST /v1/tests` (SSE auto-stream if UI; or via curl)
7. **Controls** → `POST /v2/runs/{run_id}/control` (`pause|resume|abort`)
8. **Findings** → `POST /v2/runs/{run_id}/findings` (bulk)
9. **Artifacts** → `POST /v2/runs/{run_id}/artifacts` (multipart)
10. **Reports** → `GET /v2/reports/run/{run_id}.{json|md|html}`

See **scripts/smoke.sh** for an end‑to‑end test.

---

## 7) CLI Smoke Test

```bash
./scripts/smoke.sh
```

What it does:
- Health, Catalog, Packs
- Create Engagement
- Validate selection (+ quota/OPA feedback)
- Create Plan, Start Run
- Pause/Resume/Abort (demo)
- Ingest 2 sample findings
- Export report.md + report.html

> Requires Docker stack running and `jq` installed.

---

## 8) Postman Collection

Import `postman/AI-Testing.postman_collection.json`. Set variables:
- `baseUrl`: `http://localhost:8080`
- `devUser`, `devEmail`, `tenantId` (pre-request script injects headers)

---

## 9) Testing & Troubleshooting

**Migrations fail?**  
`docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head`

**Clean DB (destructive!)**  
`./scripts/reset_db.sh` then re‑run `up` and migrations.

**CORS/UI can’t reach API?**  
The API already allows `*` in CORS; ensure `VITE_API_BASE` points to the API.

**OPA denies**  
Edit `policies/policy.rego` or submit an **approval** → `/v2/approvals`.

**Over quota**  
Update tenant quota → `/v2/quotas`.

---

## 10) Security Notes

- Every table is RLS-protected using the Postgres GUC `app.current_tenant` (set per-request).
- Approvals are required for **intrusive** tests; OPA policy enforces this at plan time.
- The platform is designed for authorized security testing only.

---

## 11) Contributing / Branching

- Use feature branches (e.g., `batch7-docs-dx`).
- Keep DB changes in Alembic `versions/` and bump API minor version in `app_v2.py`.
- For UI changes, update `infra/docker-compose.ui.yml` when adding envs.

---

## 12) Roadmap (next)

- Agent Execution Bus + Sandbox adapters (Kali/Windows/macOS)
- Remote agent bootstrap & secure tunnels
- Advanced cost/time estimator and scheduling windows
- Report templates per engagement type with SLA-ready sections
