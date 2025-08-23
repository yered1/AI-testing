# Delta v0.9.5 — Agent Artifacts + Lease2 (additive)

Adds:
- **/v2/agents/lease2**: extended lease API (returns run_id, plan_id, engagement_id).
- **/v2/jobs/{job_id}/artifacts**: agent-authenticated artifact upload (stored under EVIDENCE_DIR).
- **v2 agents** for ZAP and Nuclei that support `lease2` and auto-upload generated artifacts.
- **Smoke**: `scripts/smoke_artifacts_v095.sh` to verify end-to-end uploads.

Apply:
```bash
git checkout -b overlay-v095
unzip -o ~/Downloads/ai-testing-overlay-v095.zip
git add -A && git commit -m "v0.9.5 overlay: lease2 + agent artifact upload + v2 agents"
bash scripts/enable_routers_v095.sh   # one-time: append router includes
```

Run:
```bash
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# (optional) persist evidence
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.evidence.yml up -d

# token + agents
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens   -H 'Content-Type: application/json' -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"tenant_id":"t_demo","name":"zapv2"}' | jq -r .token)
AGENT_TOKEN="$TOKEN" bash scripts/agent_zap_v2_up.sh

# smoke
API=http://localhost:8080 TENANT=t_demo bash scripts/smoke_artifacts_v095.sh
```

Notes:
- ZAP v2 agent uploads `zap_report.html` and `zap_report.json` as artifacts if present.
- Nuclei v2 agent uploads `nuclei.jsonl` artifact if produced.
- Agents first try `lease2`; if unavailable, they fall back to the original `lease` (uploads then skipped due to missing job->run mapping).
