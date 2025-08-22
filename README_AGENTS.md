## Agents & Jobs (new in 0.6.0)

### 1) Create an agent token (admin)
```bash
curl -s -X POST http://localhost:8080/v2/agent_tokens \
  -H 'Content-Type: application/json' \
  -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo' \
  -d '{"tenant_id":"t_demo","name":"dev1","expires_in_days":30}' | jq .
# => copy .token
```

### 2) Start a dev agent (Docker)
Edit `infra/docker-compose.v2.yml` `agent_dev1` env `AGENT_TOKEN=<paste token>` then:
```bash
docker compose -f infra/docker-compose.v2.yml up --build -d agent_dev1
docker compose -f infra/docker-compose.v2.yml logs -f agent_dev1
```

### 3) Create a plan & start a run
Jobs are created for each plan step. The agent leases a job, runs the mapped adapter (echo/http), posts events and completion.

> In production, catalog adapters map to real tools (nmap, nuclei, zap, etc.) and agents run with hardened profiles.
