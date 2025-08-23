# Delta v0.9.8 — Code Review (Semgrep) + Artifact Downloads + UI page (additive)

Adds:
- **Semgrep agent** (`agents/semgrep_agent`, `infra/agent.semgrep.Dockerfile`, `infra/docker-compose.agents.semgrep.yml`, `scripts/agent_semgrep_up.sh`).
- **Catalog**: `code_semgrep_default` test + pack `default_code_review`.
- **Artifact download endpoint**: `GET /v2/artifacts/{artifact_id}/download` (agent or user auth).
- **UI Code Review page**: `/ui/code` with create→plan→run→upload flow.
- **Enable script**: `scripts/enable_code_review_v098.sh` to mount routers.
- **Smoke**: `scripts/smoke_code_review_v098.sh`.

Quickstart:
```bash
# Core up & migrate
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# Mount routers
bash scripts/enable_code_review_v098.sh

# Agent token + start
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json' -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"semgrep1"}' | jq -r .token)
AGENT_TOKEN="$TOKEN" bash scripts/agent_semgrep_up.sh

# Try UI
open http://localhost:8080/ui/code  # or http://localhost:8081/ui/code behind OIDC proxy

# CLI smoke
API=http://localhost:8080 TENANT=t_demo bash scripts/smoke_code_review_v098.sh
```
