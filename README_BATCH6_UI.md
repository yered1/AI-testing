
# Batch 6 — Minimal Web UI

Adds a lightweight UI to manage engagements, pick tests (checkbox packs), validate/preview plans,
start runs, view **live events (SSE)**, manage **quotas/approvals**, and **ingest findings / upload artifacts**.

## Run
```bash
# Orchestrator + DB + OPA
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# UI (port 3000)
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.ui.yml up --build -d ui
open http://localhost:3000
```
> The UI uses DEV headers (user/email/tenant) which you can edit at the top of the page.
> Ensure Batch 5 (findings/reporting) migration is applied for findings/report views.
