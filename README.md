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
