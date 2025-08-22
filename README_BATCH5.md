# Batch 5 — Findings & Reporting v1 (v2)

Adds **tenant‑scoped findings storage**, evidence attachments (URL/text), and **report generation** (Markdown/JSON)
for an engagement. The API remains additive and v1-safe.

## What’s included
- **DB migration**: `findings`, `finding_evidence`, and `reports` tables (RLS-enabled).
- **Endpoints**:
  - `POST /v2/findings` — ingest a finding (from agents or humans).
  - `GET /v2/findings` — list/filter by engagement/run/severity/status.
  - `GET /v2/findings/{id}` — retrieve one.
  - `POST /v2/findings/{id}/status` — update status / resolution.
  - `POST /v2/findings/{id}/evidence` — add evidence (URL or text snippet).
  - `GET /v2/reports/engagement/{engagement_id}` — generate a Markdown or JSON report on the fly.
- **Template**: `orchestrator/templates/report.md.j2` (Jinja2).
- **Dependencies**: adds `Jinja2` to `requirements-extra.txt`.

## Install / Update
```bash
git checkout -b batch5-findings-reporting
unzip -o ~/Downloads/ai-testing-batch5.zip
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head
open http://localhost:8080/docs
```

## Quick smoke

```bash
# 1) Create engagement (if not created)
ENG=$(curl -s -X POST http://localhost:8080/v1/engagements   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"name":"Web App","tenant_id":"t_demo","type":"web","scope":{"in_scope_domains":["app.example.com"],"in_scope_cidrs":[],"out_of_scope":[],"risk_tier":"safe_active","windows":[]}}' | jq -r .id)

# 2) Create a simple plan & run (optional; findings can be linked to a run)
cat > sel.json <<'JSON'
{"selected_tests":[{"id":"web_owasp_top10_core"}],"agents":{},"risk_tier":"safe_active"}
JSON
PLAN=$(curl -s -X POST http://localhost:8080/v1/engagements/$ENG/plan   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   --data-binary @sel.json | jq -r .id)
RUN=$(curl -s -X POST http://localhost:8080/v1/tests   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d "{"engagement_id":"$ENG","plan_id":"$PLAN"}" | jq -r .id)

# 3) Ingest a finding (link to engagement + optional run)
curl -s -X POST http://localhost:8080/v2/findings   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d "{"tenant_id":"t_demo","engagement_id":"$ENG","run_id":"$RUN","title":"Reflected XSS on /search","severity":"high","category":"web","owasp":"A03:2021","cwe":"CWE-79","cvss":"8.2","description":"User input reflected without encoding.","recommendation":"Encode output; adopt CSP.","affected_assets":[{"url":"https://app.example.com/search?q=<script>alert(1)</script>"}]}" | jq .

# 4) Add evidence (URL or text)
FID="<paste finding id>"
curl -s -X POST http://localhost:8080/v2/findings/$FID/evidence   -H 'Content-Type: application/json'   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   -d '{"type":"url","value":"https://s3.example.com/proof/xss.mp4"}' | jq .

# 5) Generate Markdown report
curl -s "http://localhost:8080/v2/reports/engagement/$ENG?format=md"   -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo'   | sed -n '1,80p'
```
