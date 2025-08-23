# Delta v1.4.2 — Kali OS Agent (HTTPS pull) + Safer Cleanup (additive)

**Highlights**
- **Kali OS Agent** that runs natively on Kali, connects to the orchestrator via the existing **HTTPS agent bus** (v2) and executes **allowlisted** offsec tools locally. Uploads artifacts and posts results back.
- **Catalog** tests & pack targeting `kali_os` agent kind.
- **Cleanup tools:** stronger but **safe** cache/junk cleanup (dry-run by default), repo doctor report, stricter `.gitignore` merging.

## Install the Kali OS Agent (on your Kali box)
```bash
# From your repo root on the Kali host (or copy the files over):
# 1) Create a token
TOKEN=$(curl -s -X POST http://ORCH_HOST:8080/v2/agent_tokens \
  -H 'Content-Type: application/json' \
  -H 'X-Dev-User: dev' -H 'X-Dev-Email: dev@example.com' -H 'X-Tenant-Id: t_demo' \
  -d '{"tenant_id":"t_demo","name":"kali-os"}' | jq -r .token)

# 2) Install the agent as a systemd service
ORCH_URL=http://ORCH_HOST:8080 TENANT_ID=t_demo AGENT_TOKEN="$TOKEN" \
bash scripts/install_kali_os_agent.sh

# 3) Tail logs
sudo journalctl -u kali-os-agent -f
```

**Active scans** are **dry-run** by default. Explicitly allow:
```bash
sudo sed -i 's/ALLOW_ACTIVE_SCAN=0/ALLOW_ACTIVE_SCAN=1/' /etc/kali-os-agent/config.env
sudo systemctl restart kali-os-agent
```

**Allowlist tools** in `/etc/kali-os-agent/tools.yaml` (seeded with `nmap_tcp_top_1000`, `ffuf_dirb`, `gobuster_dir`, `sqlmap_basic`).

## Using the remote Kali tests
Use the **Test Builder** or curl to select the new tests / pack:
- Tests: `remote_kali_nmap_tcp_top_1000`, `remote_kali_run_tool`
- Pack: `default_remote_kali_min`

The orchestrator will create jobs targeted to `kali_os` agents; your agent polls `/v2/agents/lease`, runs the command, uploads artifacts, and completes the job.

## Cleanup & repo hygiene
```bash
# Inspect junk & large files
bash scripts/run_repo_doctor_v142.sh

# Safe cleanup (dry-run by default). Apply deletions with DRY_RUN=0
bash scripts/cleanup_strict_v142.sh
DRY_RUN=0 bash scripts/cleanup_strict_v142.sh

# Strengthen .gitignore
bash scripts/merge_gitignore_v142.sh
```

> These scripts **do not** remove any product features. They only remove caches and platform cruft. Docs/merge scripts remain unless you archive them manually.
