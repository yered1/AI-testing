# AI Testing Platform — Batch 1 (Auth + DB + RLS-ready, v2 drop-in)

This package **adds** a DB-backed, OIDC/MFA-ready, tenant-isolated API alongside your current code (served from `orchestrator/app_v2.py`) and a second Docker Compose stack with Postgres.

## Run with Docker
```bash
cp orchestrator/.env.example orchestrator/.env
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
# Open http://localhost:8080/docs
```

## Local dev
```bash
export DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/ai_testing
cd orchestrator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-extra.txt
alembic upgrade head
uvicorn app_v2:app --reload --host 0.0.0.0 --port 8080
```

## Auth modes
- **DEV** (`DEV_BYPASS_AUTH=true`): use headers `X-Dev-User`, `X-Dev-Email`, `X-Tenant-Id`.
- **OIDC**: set `OIDC_ISSUER`, `OIDC_AUDIENCE`; with `REQUIRE_MFA=true` the token must include `amr=["mfa"| "otp"]`.

## Endpoints
- `GET /health`
- `GET /v1/catalog`
- `POST /v1/engagements`
- `POST /v1/engagements/{id}/plan`
- `POST /v1/tests`
- `GET /v1/tests/{run_id}`
