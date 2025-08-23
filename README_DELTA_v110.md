# Delta v1.1.0 — Enhanced Reports (HTML/MD/PDF) with Taxonomy & CVSS (additive)

Adds:
- **Enhanced report endpoints**: `/v2/reports/enhanced/run/{id}.{html|md|pdf}`
- **Taxonomy/CVSS**: OWASP Top 10 (2021) mapping, keyword heuristics to tag findings, and CVSS v3.1 base score from vector (if provided).
- **Templates**: `orchestrator/report_templates/*`
- **Enable**: `scripts/enable_reports_enhanced_v110.sh`
- **Smoke**: `scripts/smoke_reports_enhanced_v110.sh`

## Use
```bash
# Enable router
bash scripts/enable_reports_enhanced_v110.sh

# Start core & migrate
docker compose -f infra/docker-compose.v2.yml up --build -d
docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

# (optional) start reporter & set REPORTER_URL
docker compose -f infra/docker-compose.reports.yml up --build -d reporter
# add to orchestrator env: REPORTER_URL=http://reporter:8080  (compose override or env)
# then restart orchestrator

# Smoke
API=http://localhost:8080 TENANT=t_demo bash scripts/smoke_reports_enhanced_v110.sh
```
