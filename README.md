# AI Pentest Platform (Starter Skeleton)

> **Status**: walking-skeleton scaffold — FastAPI orchestrator, JSON Schemas, sample Test Catalog, basic OPA policy stub, and agent stubs.  
> This is meant to get you running quickly; replace in-memory stores with Postgres and wire real agents as you iterate.

## What’s here

- **orchestrator/**: FastAPI app exposing minimal endpoints
  - `/health`, `/v1/catalog`, `/v1/engagements`, `/v1/engagements/{id}/plan`, `/v1/tests`, `/v1/tests/{id}`
- **schemas/**: JSON Schemas (Plan DSL, Test Catalog item, Event, Finding)
- **catalog/**: sample test definitions (checkbox-ready)
- **policies/**: OPA/Rego policy stub for scope & risk
- **agents/**: Python stubs for Kali gateway and cross-platform agent
- **infra/**: docker-compose to run orchestrator quickly

## Quick start

```bash
# 1) Using Docker (recommended for a quick spin)
docker compose -f infra/docker-compose.yml up --build

# 2) Or run locally (Python 3.10+)
cd orchestrator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8080

# Open docs: http://localhost:8080/docs
```

## Next steps (suggested)
- Replace in-memory stores with Postgres + SQLAlchemy/RLS.
- Hook OPA decision checks before plan/run creation.
- Implement WebSocket/SSE event streams for live progress.
- Add authentication/authorization (OIDC + MFA) — this skeleton is unauthenticated by design for local testing.
- Expand Test Catalog and map to real tool adapters in agents.

**Legal note:** Use only with explicit written authorization (ROE/LoA). You are responsible for lawful use.
