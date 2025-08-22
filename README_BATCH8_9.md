# Updates — Batch 8 & 9

This overlay adds:
- **Batch 8**: Agent Execution Bus (enrollment tokens, registration, jobs, events)
- **Batch 9**: AI Brain (auto-plan suggestions, feedback API, HTTP provider hook)

## Apply
```bash
git checkout -b batch8-9-agents-brain
unzip -o ~/Downloads/ai-testing-batch8-agents.zip
unzip -o ~/Downloads/ai-testing-batch9-brain.zip
git add -A && git commit -m "Batch 8+9: agents bus + AI brain (auto plan + feedback)"
```

## Migrate
```bash
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
```

## Dev agent
```bash
# Create token
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"dev1"}' | jq -r .token)

# Launch agent
AGENT_TOKEN=$TOKEN docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.yml up --build -d agent_dev1
```

## Auto-plan
```bash
# Ask the brain to suggest a plan
curl -s -X POST http://localhost:8080/v2/engagements/$ENG/plan/auto   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"preferences":{"packs":["pack.standard_network"]},"risk_tier":"safe_active"}' | jq .
```

### Optional external LLM
Set env vars (or Docker env) to use an external HTTP LLM service that returns `{tests: [ids], explanation: "..."}`:
- `LLM_HTTP_ENDPOINT` — URL to POST JSON `{ engagement, catalog }`
- `LLM_HTTP_TOKEN` — Bearer token (optional)
If not set, the **heuristic** brain is used.
