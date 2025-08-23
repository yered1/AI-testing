
# Delta v1.4.0 — Repo Doctor + Safe Cleanup + Agent SDK + **Kali Remote Agent** (additive)

This drop focuses on **completeness & cleanup** and your key feature: a **remote agent that controls an OS with offsec tools** (Kali). No features removed.

## What's included
- **Repo Doctor** (`scripts/repo_doctor.py`, `scripts/run_repo_doctor.sh`)  
  Audit includes/routers/endpoints/agents. Produces a consolidation plan and lists *only safe junk* (pyc, __pycache__, .pytest_cache, .DS_Store).
- **Safe Cleanup** (`scripts/cleanup_safe.sh`)  
  Deletes *only* cache/temp files. No source/features touched.
- **Agent SDK** (`orchestrator/agent_sdk/`)  
  Shared HTTP client for agents (register, heartbeat, lease/lease2, events, complete, artifact upload).
- **Kali Remote Agent** (`agents/kali_remote_agent`)  
  SSH into a remote Kali box and run allowed tools (allowlist in `tools.yaml`). Uploads results via the existing artifact pipeline.
  - Dockerfile: `infra/agent.kali.remote.Dockerfile`
  - Compose: `infra/docker-compose.agents.kali.remote.yml`
  - Runner: `scripts/agent_kali_remote_up.sh`

## Usage

### Safe cleanup (optional)
```bash
bash scripts/cleanup_safe.sh
# or dry-run audit
bash scripts/run_repo_doctor.sh
```

### Start the Kali remote agent
Create a token:
```bash
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"kali-remote"}' | jq -r .token)
```

Set SSH details (use base64 key or password; key preferred):
```bash
export AGENT_TOKEN="$TOKEN"
export SSH_HOST=YOUR.KALI.IP
export SSH_USER=kali
export SSH_KEY_BASE64=$(base64 -w0 ~/.ssh/id_rsa)   # or set SSH_PASSWORD
bash scripts/agent_kali_remote_up.sh
```

### Using the agent
Submit jobs via your planner/Builder using adapters:
- `run_tool` with params `{"name":"nmap_tcp_top_1000","args":"-vv 192.0.2.10"}` (see `agents/kali_remote_agent/tools.yaml`)
- `nmap_tcp_top_1000` with `{"target":"192.0.2.10"}` (honors `ALLOW_ACTIVE_SCAN`)

Artifacts (stdout/logs) are uploaded to the run’s evidence via `/v2/jobs/{job_id}/artifacts`.

> **Safety**: Active scanning only runs when `ALLOW_ACTIVE_SCAN=1`. Keep the tool allowlist tight in `tools.yaml`.

