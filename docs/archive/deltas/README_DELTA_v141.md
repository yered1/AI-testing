# Delta v1.4.1 — Cleanup & Completeness (additive)

Adds:
- **Repo Doctor** (`scripts/repo_doctor_v141.py`, `scripts/run_repo_doctor_v141.sh`) to report junk & missing router includes.
- **Safe Cleanup** (`scripts/cleanup_safe_v141.sh`) removes macOS junk & Python caches.
- **Bootstrap Fixer** (`scripts/fix_bootstrap_includes_v141.py/.sh`) appends any missing router imports/includes to `bootstrap_extras.py`.
- **.gitignore merge** (`templates/gitignore.append`, `scripts/merge_gitignore_v141.sh`).
- **Optional Archiver** (`scripts/archive_docs_v141.sh`) to move `README_DELTA_*` and old `merge_readme_*` scripts into `docs/archive/` and `scripts/archive/`.
- **Kali Remote Agent** (`agents/kali_remote_agent`) + compose & launcher.

Quickstart:
```bash
# 1) Audit & clean
bash scripts/run_repo_doctor_v141.sh
bash scripts/cleanup_safe_v141.sh
bash scripts/fix_bootstrap_includes_v141.sh
bash scripts/merge_gitignore_v141.sh

# 2) (Optional) archive deltas
CONFIRM=1 bash scripts/archive_docs_v141.sh

# 3) Start remote Kali agent
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"kali-remote"}' | jq -r .token)

AGENT_TOKEN="$TOKEN" SSH_HOST=<ip/dns> bash scripts/agent_kali_remote_up.sh
```
