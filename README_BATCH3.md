# Batch 3 — Quotas, Approvals, and OPA Enforcement (v2)

This batch extends **v2** with:
- **Quotas** (per-tenant monthly credits, per-engagement caps)
- **Approvals** (risk-tier gates for intrusive steps)
- **OPA sidecar** enforcement (scope + risk checks at plan time)
- **Estimate-aware run blocking** (deny if quota exhausted; show reasons)

> Drop-in overlay. Unzip at repo root (`AI-testing/`) with `unzip -o` and follow steps below.

## Run / Update

```bash
# 1) Ensure v2 env
cp orchestrator/.env.example orchestrator/.env  # if not already present

# 2) Bring up v2 stack (adds OPA sidecar)
docker compose -f infra/docker-compose.v2.yml up --build -d

# 3) Run migrations (adds quotas/approvals tables)
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# 4) Docs
open http://localhost:8080/docs
```

## Quick smoke (DEV bypass headers required)
```bash
TEN=t_demo
# Create (or reuse) an engagement id ENG from previous steps.

# Set a quota (e.g., 100 credits, cap per plan 30)
curl -s -X POST http://localhost:8080/v2/quotas   -H 'Content-Type: application/json'   -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: $TEN"   -d '{"tenant_id":"t_demo","monthly_budget":100,"per_plan_cap":30}' | jq .

# Validate selection (shows estimate + over_quota if exceeded)
curl -s -X POST http://localhost:8080/v2/engagements/$ENG/plan/validate   -H 'Content-Type: application/json'   -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: $TEN"   --data-binary @sel.json | jq .

# Request approval if plan contains intrusive steps
curl -s -X POST http://localhost:8080/v2/approvals   -H 'Content-Type: application/json'   -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: $TEN"   -d '{"tenant_id":"t_demo","engagement_id":"'$ENG'","reason":"Allow intrusive checks for window 1"}' | jq .
```

## Notes
- OPA is mounted with `policies/` and called at plan-validate time.
- If **any step** has `risk_tier: "intrusive"`, an **approval** is required before starting the run.
- Quota enforcement happens at plan time and run start; usage is accrued per run using the estimate.
