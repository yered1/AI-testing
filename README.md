# AI Pentest Platform

This repository now contains two runnable variants:

- **v1 (starter skeleton):** In-memory FastAPI orchestrator (for quick local tests).
- **v2 (DB + Auth + RLS):** Postgres-backed orchestrator with OIDC/MFA-ready auth and tenant isolation.
- **Batch 2:** Test Catalog expansion + **Dry-run validator** + **Estimate** + **Plan Preview** + **Test Packs**.

---

## Quick start (v2: recommended)

```bash
# From repo root
cp orchestrator/.env.example orchestrator/.env

# Bring up Postgres + Orchestrator (v2)
docker compose -f infra/docker-compose.v2.yml up --build -d

# Run DB migrations
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# Open the API docs
open http://localhost:8080/docs
```

### Smoke test (DEV auth bypass on)
```bash
# Catalog
curl -s http://localhost:8080/v1/catalog   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo' | jq '.'

# Catalog packs
curl -s http://localhost:8080/v1/catalog/packs   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo' | jq '.'

# Create an engagement
curl -s -X POST http://localhost:8080/v1/engagements   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"name":"Demo Net","tenant_id":"t_demo","type":"network","scope":{"in_scope_domains":["example.com"],"in_scope_cidrs":["10.0.0.0/24"],"out_of_scope":[],"risk_tier":"safe_active","windows":[]}}' | jq '.'
```

### Validate + Estimate (Batch 2)
```bash
ENG="eng_..."
cat > sel.json <<'JSON'
{
  "selected_tests":[
    {"id":"network.discovery.ping_sweep"},
    {"id":"network.nmap.tcp_top_1000"},
    {"id":"web.owasp.top10.core", "params":{"url":"https://app.example.com"}},
    {"id":"api.schema.conformance", "params":{"openapi_url":"https://api.example.com/openapi.json"}}
  ],
  "agents":{"strategy":"recommended"},
  "risk_tier":"safe_active"
}
JSON

curl -s -X POST http://localhost:8080/v2/engagements/$ENG/plan/validate   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   --data-binary @sel.json | jq '.'
```

### Preview (no persist)
```bash
curl -s -X POST http://localhost:8080/v2/engagements/$ENG/plan/preview   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   --data-binary @sel.json | jq '.'
```

### Create plan + start a run (v2 core)
```bash
# Create plan (persists)
curl -s -X POST http://localhost:8080/v1/engagements/$ENG/plan   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   --data-binary @sel.json | jq '.'

# Start a run (placeholder executor)
PLAN="plan_..."
curl -s -X POST http://localhost:8080/v1/tests   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d "{"engagement_id":"$ENG","plan_id":"$PLAN"}" | jq '.'
```

---

## Batch 2 features
- **/v2/engagements/{id}/plan/validate**: dry-run validation (existence, prereqs, conflicts, required inputs, basic scope checks), plus **estimates** for runtime & cost.
- **/v2/engagements/{id}/plan/preview**: show executable **Plan** (steps/order) without saving.
- **/v1/catalog/packs**: fetches **test packs** (e.g., OWASP Top 10, Standard Network) for the checkbox UI.

> Notes: Estimation uses catalog-provided estimators and parses CIDRs in scope to approximate host counts (capped). Real agent capacity and quotas will refine these numbers in later batches.
