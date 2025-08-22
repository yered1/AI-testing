# Agents (Batch 8)

This adds a secure **Agent Execution Bus**:

- Create one-time **enrollment tokens**: `POST /v2/agent_tokens`
- Agents **register**: `POST /v2/agents/register` using the token → receive `agent_id` + `agent_key`
- Agents **heartbeat**: `POST /v2/agents/heartbeat`
- Agents **lease** next job: `POST /v2/agents/lease`
- Agents **emit progress**: `POST /v2/jobs/{id}/events`
- Agents **complete** a job: `POST /v2/jobs/{id}/complete`

### Run a dev agent

```bash
# 1) Create an agent token
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens \
  -H 'Content-Type: application/json' \
  -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo' \
  -d '{"tenant_id":"t_demo","name":"dev1"}' | jq -r .token)

# 2) Start dev agent
AGENT_TOKEN=$TOKEN docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.yml up --build -d agent_dev1
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.yml logs -f agent_dev1
```
