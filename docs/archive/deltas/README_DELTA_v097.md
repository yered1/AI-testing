# Delta v0.9.7 — Minimal UI (additive)

Adds a lightweight UI served by the orchestrator:
- Routes: `/ui`, `/ui/new`, `/ui/runs/{run_id}`, `/ui/admin`
- Static assets at `/ui/static/*` (JS+CSS)
- Uses existing API endpoints (catalog, plan/validate, create plan, start run, SSE events, artifacts, reports, bundle)
- No overwrites; mounted via `bootstrap_extras.py`

## Apply
```bash
git checkout -b overlay-v097
unzip -o ~/Downloads/ai-testing-overlay-v097.zip
git add -A && git commit -m "v0.9.7 overlay: minimal UI (additive)"
bash scripts/enable_ui_v097.sh   # mounts the UI router
```

## Run
```bash
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
open http://localhost:8080/ui
# or, if using OIDC/MFA proxy: http://localhost:8081/ui
```
