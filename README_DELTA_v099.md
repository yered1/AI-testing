
# Delta v0.9.9 — Mobile APK Static Analysis (Androguard) + UI page (additive)

Adds:
- **Mobile APK agent** (`agents/mobile_apk_agent`) with lease2 support, downloads APK from run artifacts, analyzes with **androguard**, uploads `apk_summary.json` and (best effort) `AndroidManifest.xml`.
- **Agent container/compose**: `infra/agent.mobile_apk.Dockerfile`, `infra/docker-compose.agents.mobile_apk.yml`, `scripts/agent_mobile_apk_up.sh`.
- **Catalog**: test `mobile_apk_static_default` and pack `default_mobile_static`.
- **UI**: `/ui/mobile` to guide APK upload → auto plan → run → results.
- **Smoke**: `scripts/smoke_mobile_v099.sh` (set `APK=/path/to/app.apk`).

## Use

```bash
# Apply overlay
unzip -o ai-testing-overlay-v099.zip
bash scripts/enable_mobile_v099.sh

# Start core
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# Start agent (after creating a token)
TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens  -H 'Content-Type: application/json' -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'  -d '{"tenant_id":"t_demo","name":"mobile_apk"}' | jq -r .token)
AGENT_TOKEN="$TOKEN" bash scripts/agent_mobile_apk_up.sh

# UI
open http://localhost:8080/ui/mobile
```

> Notes: The analysis is **static** and safe. Provide an APK via the UI or `POST /v2/runs/{id}/artifacts` with label `mobile_apk`. The agent prefers `/v2/agents/lease2` to discover the run context; falls back to legacy lease if needed.
