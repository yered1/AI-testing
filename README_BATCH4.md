# Batch 4 — Live Progress (SSE), Run Controls, Slack Notifications (v2)

This batch extends **v2** with real-time **Server-Sent Events (SSE)** for run progress, **Pause/Resume/Abort** controls,
and optional **Slack** notifications. It remains non-destructive (v1 unchanged).

## What’s included
- **DB migration**: `run_events` table (tenant-scoped, RLS-enabled) for streaming + history.
- **SSE endpoint**: `GET /v2/runs/{run_id}/events` (text/event-stream).
- **Run controls**: `POST /v2/runs/{run_id}/control` → `{ "action": "pause" | "resume" | "abort" }`.
- **Simulation mode**: When `SIMULATE_PROGRESS=true`, the orchestrator simulates step events after `POST /v1/tests`.
- **Slack (optional)**: Set `SLACK_WEBHOOK` to receive run started/completed/failed messages.

## Install / Update
```bash
# From repo root
git checkout -b batch4-live-progress
unzip -o ~/Downloads/ai-testing-batch4.zip

# Migrate DB
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# Docs
open http://localhost:8080/docs
```

## Smoke tests
```bash
# Create engagement (if needed)
ENG=$(curl -s -X POST http://localhost:8080/v1/engagements   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"name":"Demo Net","tenant_id":"t_demo","type":"network","scope":{"in_scope_domains":["example.com"],"in_scope_cidrs":["10.0.0.0/24"],"out_of_scope":[],"risk_tier":"safe_active","windows":[]}}' | jq -r .id)

# Build a plan
cat > sel.json <<'JSON'
{"selected_tests":[{"id":"network.discovery.ping_sweep"},{"id":"network.nmap.tcp_top_1000"}],"agents":{"strategy":"recommended"},"risk_tier":"safe_active"}
JSON
PLAN=$(curl -s -X POST http://localhost:8080/v1/engagements/$ENG/plan   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   --data-binary @sel.json | jq -r .id)

# Start a run
RUN=$(curl -s -X POST http://localhost:8080/v1/tests   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d "{"engagement_id":"$ENG","plan_id":"$PLAN"}" | jq -r .id)

# Stream live events (keep open)
curl -N http://localhost:8080/v2/runs/$RUN/events   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'

# Pause → Resume → Abort (in a separate terminal)
curl -s -X POST http://localhost:8080/v2/runs/$RUN/control   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"action":"pause"}' | jq .

curl -s -X POST http://localhost:8080/v2/runs/$RUN/control   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"action":"resume"}' | jq .
```
