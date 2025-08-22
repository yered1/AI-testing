# PDF Reports (additive)

Two options:
1) **Script** (recommended): Start reporter with `docker compose -f infra/docker-compose.reports.yml up -d reporter` then run `scripts/render_pdf_from_api.sh <RUN_ID>`.
2) **API**: POST to `http://localhost:8082/render/pdf` with `{"url": "http://orchestrator:8080/v2/reports/run/<RUN>.html"}` or raw `html`.

The reporter isolates wkhtmltopdf dependencies from your orchestrator image.
