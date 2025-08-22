# Auth Setup (OIDC + MFA via oauth2-proxy) — Additive

This stack puts **oauth2-proxy** and **Nginx** in front of the Orchestrator. Your IdP (Okta / Azure AD / Google) handles **OIDC + MFA**; oauth2-proxy injects headers that the Orchestrator already accepts in dev mode (`X-Dev-User`, `X-Dev-Email`, `X-Tenant-Id`).

## Steps
1. Copy and edit env:
   ```bash
   cp infra/auth/.env.auth.example infra/auth/.env.auth
   # fill CLIENT_ID, CLIENT_SECRET, OIDC_ISSUER_URL, COOKIE_SECRET, etc.
   ```
2. Start auth stack:
   ```bash
   docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.auth.yml up -d reverse-proxy oauth2-proxy
   open http://localhost:8081
   ```
3. In production, remove `X-Dev-*` bypass and map IdP claims to tenant header, or persist tenants per user in DB.

> This is additive: no change to Orchestrator image required.
