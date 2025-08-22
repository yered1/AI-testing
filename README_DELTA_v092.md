# Delta v0.9.2 — OIDC/MFA proxy + PDF reporter (additive)

Adds:
- **OIDC/MFA** front door via oauth2-proxy + Nginx: `infra/docker-compose.auth.yml`, `infra/auth/*`, `scripts/auth_stack_up.sh`, docs in `docs/AUTH_SETUP.md`.
- **PDF Reporter** microservice: `services/reporter`, `infra/reporter.Dockerfile`, `infra/docker-compose.reports.yml`, `scripts/render_pdf_from_api.sh`, docs in `docs/REPORTS_PDF.md`.

Quick start:
```bash
# Auth
cp infra/auth/.env.auth.example infra/auth/.env.auth
# edit .env.auth with your IdP details
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.auth.yml up -d reverse-proxy oauth2-proxy
open http://localhost:8081

# Reporter
docker compose -f infra/docker-compose.reports.yml up --build -d reporter
bash scripts/render_pdf_from_api.sh <RUN_ID>
```
