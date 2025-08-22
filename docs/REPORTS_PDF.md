# PDF Reports (additive microservice)

Run the **Reporter** service (wkhtmltopdf inside a container), then convert the API's HTML report to PDF.

```bash
# Start reporter (one time)
docker compose -f infra/docker-compose.reports.yml up --build -d reporter

# Generate PDF for a run
bash scripts/render_pdf_from_api.sh RUN_ID
```

This avoids modifying the Orchestrator image and keeps dependencies isolated.
