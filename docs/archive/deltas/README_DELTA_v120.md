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
