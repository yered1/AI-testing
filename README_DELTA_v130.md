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
