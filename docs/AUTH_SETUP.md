# OIDC/MFA via oauth2-proxy + Nginx (additive)

This stack puts an auth gate in front of the orchestrator without changing backend code.

## Steps
1. `cp infra/auth/.env.auth.example infra/auth/.env.auth` and fill issuer/client/secret/cookie secret.
2. Start: `docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.auth.yml up -d reverse-proxy oauth2-proxy`
3. Visit `http://localhost:8081` — you'll be redirected to your IdP (with MFA if configured).
4. The proxy maps IdP headers to backend dev headers:
   - `X-Auth-Request-User` → `X-Dev-User`
   - `X-Auth-Request-Email` → `X-Dev-Email`
   - `X-Tenant-Id` defaults to `t_demo` (adjust Nginx config).

In production, map tenant from a claim (e.g., `org_id`) and turn off any dev bypass on the backend.
