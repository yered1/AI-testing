# Delta v0.9.0 — Extended Dev Agent + OPA v2 + Postman (additive)

Adds:
- **Dev Agent (extended)** with pluggable adapters (`echo`, `nmap_tcp_top_1000`) and dry‑run by default (`ALLOW_ACTIVE_SCAN=0`).
- **Agent compose**: `infra/docker-compose.agents.ext.yml`, Dockerfile installs `nmap`.
- **OPA policy v2**: `policies/policy.v2.rego` with risk + quota checks.
- **Postman collection**: `docs/postman/AI-testing.postman_collection.json`.
- **Scripts**: `scripts/agent_devext_up.sh`, `scripts/cleanup_evidence.sh`.

## Use

1) Build core + migrate
```bash
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
```

2) (Optional) Persist evidence
```bash
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.evidence.yml up -d
```

3) Create an agent token, then start the extended agent
```bash
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json' -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"devext"}' | jq -r .token)

AGENT_TOKEN="$TOKEN" bash scripts/agent_devext_up.sh
# To actually run nmap (be sure you're authorized), also set ALLOW_ACTIVE_SCAN=1
# ALLOW_ACTIVE_SCAN=1 AGENT_TOKEN="$TOKEN" bash scripts/agent_devext_up.sh
```

4) Postman: import `docs/postman/AI-testing.postman_collection.json`.

> **Safety**: By default the agent is **dry‑run** for active scans. Enable only when you have written permission for the target.
