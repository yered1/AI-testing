# Batch 6 — Minimal Web UI (React + Vite)

A minimal UI for the v2 orchestrator. Supports: dev headers, engagement creation, catalog/pack selection,
validate/preview, create plan, start run with live SSE, run controls, artifact upload, and report exports.

## Install / Update
```bash
git checkout -b batch6-ui
unzip -o ~/Downloads/ai-testing-batch6-ui.zip
git add -A
git commit -m "Batch 6: Minimal Web UI"
```

## Run (with existing v2 stack)
```bash
# Orchestrator + OPA + DB
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# UI (port 3000)
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.ui.yml up --build -d ui
open http://localhost:3000
```

## Notes
- The UI uses `VITE_API_BASE` (set in `infra/docker-compose.ui.yml`) to talk to the orchestrator.
- SSE streaming uses the `fetch` streaming API so dev headers are included.
- For reports, the UI fetches content with headers and triggers client-side download.
