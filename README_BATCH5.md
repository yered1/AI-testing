# Batch 5 — Findings & Reporting v1 (v2 overlay)

Adds **findings ingestion**, **artifacts/evidence uploads**, and **report exports** (JSON/Markdown/HTML). Non‑destructive overlay to v2.

## What’s included
- **DB migration** `0004_findings_reporting.py`:
  - `findings` (tenant‑scoped, RLS): title, severity, description, assets, CWE/OWASP tags, CVSS, recommendation, status.
  - `artifacts` (tenant‑scoped, RLS): uploaded files linked to run and optionally a finding.
  - `evidence` (tenant‑scoped, RLS): structured text notes/logs for a finding.
- **Endpoints (app_v2.py)**:
  - `POST /v2/runs/{run_id}/findings` — bulk upsert (id optional; generated if missing).
  - `GET /v2/runs/{run_id}/findings` — list findings for the run.
  - `POST /v2/runs/{run_id}/artifacts` — multipart file upload; fields: `file`, `finding_id` (optional).
  - `GET /v2/reports/run/{run_id}.json|.md|.html` — exports based on current findings/artifacts.
- **Evidence store**: local path configurable via `EVIDENCE_DIR` (default `/data/evidence`), persisted with a Docker volume.
- **Templates**: `orchestrator/templates/report_run.md.j2` and `report_run.html.j2`

## Update / Run
```bash
git checkout -b batch5-findings-reporting
unzip -o ~/Downloads/ai-testing-batch5.zip

# Bring up stack & run migrations
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

open http://localhost:8080/docs
```

## Quick smoke
```bash
# 0) Assume you have ENG, PLAN, RUN created as in earlier batches

# 1) Ingest findings (bulk)
cat > findings.json <<'JSON'
[
  {
    "title": "Directory listing enabled",
    "severity": "low",
    "description": "The /static/ path exposes file listing.",
    "assets": {"urls": ["https://app.example.com/static/"]},
    "recommendation": "Disable autoindex and restrict directory browsing.",
    "tags": {"owasp": ["A5-2021"], "cwe": [548]}
  },
  {
    "title": "SSL certificate mismatch",
    "severity": "medium",
    "description": "CN does not match hostname on api endpoint.",
    "assets": {"hosts": ["api.example.com"]},
    "recommendation": "Regenerate certificate with proper SANs.",
    "tags": {"cwe": [297]}
  }
]
JSON

curl -s -X POST http://localhost:8080/v2/runs/$RUN/findings \
  -H 'Content-Type: application/json' \
  -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo' \
  --data-binary @findings.json | jq .

# 2) Upload an artifact (attach to first finding id from response)
FID="find_XXXXXXXX"  # replace
curl -s -X POST http://localhost:8080/v2/runs/$RUN/artifacts \
  -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo' \
  -F finding_id=$FID -F file=@/path/to/screenshot.png | jq .

# 3) Export report (Markdown)
curl -s http://localhost:8080/v2/reports/run/$RUN.md \
  -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo' \
  -o report.md && echo "report.md written"

# 4) Export report (HTML)
curl -s http://localhost:8080/v2/reports/run/$RUN.html \
  -H 'X-Dev-User: yered' -H 'X-Dev-Email: yered@example.com' -H 'X-Tenant-Id: t_demo' \
  -o report.html && echo "report.html written"
```
