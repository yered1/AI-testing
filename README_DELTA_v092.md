# Delta v0.9.2 — OIDC/MFA proxy + PDF reporter (additive)

Adds:
- **Auth proxy stack** (`infra/docker-compose.auth.yml`) with **oauth2-proxy** + **Nginx** (`infra/auth/*`).
- **PDF Reporter** microservice (`infra/reporter.Dockerfile`, `services/reporter/app.py`) + compose override (`infra/docker-compose.reports.yml`).
- Scripts: `scripts/auth_stack_up.sh`, `scripts/render_pdf_from_api.sh`.
- Docs: `docs/AUTH_SETUP.md`, `docs/REPORTS_PDF.md`.

## Use (auth)
```bash
cp infra/auth/.env.auth.example infra/auth/.env.auth
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.auth.yml up -d reverse-proxy oauth2-proxy
open http://localhost:8081
```

## Use (PDF)
```bash
docker compose -f infra/docker-compose.reports.yml up --build -d reporter
bash scripts/render_pdf_from_api.sh <RUN_ID>
```

All additive — your current Orchestrator and routers remain untouched.
