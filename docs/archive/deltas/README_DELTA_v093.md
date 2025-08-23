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
