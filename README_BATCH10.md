# Batch 10 — UI v2 + API listings

**What changed**
- UI v2 adds: Auto‑Plan, Quotas & Approvals panel, Recent Runs list, Agents panel, Findings tools.
- API adds: `GET /v2/runs/recent`, `GET /v2/agents`, `GET /v2/approvals`.

**Install**
```bash
git checkout -b batch10-ui-v2
unzip -o ~/Downloads/ai-testing-batch10.zip
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.ui.yml up --build -d ui
open http://localhost:3000
```
