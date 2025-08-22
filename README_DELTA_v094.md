# Delta v0.9.4 — RBAC via OIDC Groups at Proxy + OPA v4 (additive)

Adds:
- **RBAC reverse proxy** with Nginx + oauth2-proxy using groups claim:
  - `infra/docker-compose.auth-rbac.yml`
  - `infra/auth/oauth2_proxy.rbac.cfg`, `infra/auth/nginx.rbac.conf`
  - `infra/auth/.env.auth.example` (extended with `OAUTH2_PROXY_OIDC_GROUPS_CLAIM`)
  - `scripts/auth_rbac_up.sh`
  - Docs: `docs/AUTH_RBAC_MAPPING.md`
- **OPA v4 policy** (`policies/policy.v4.rego`) reflecting roles & tenant isolation.

## Start (dev)
```bash
cp infra/auth/.env.auth.example infra/auth/.env.auth
# Fill ISSUER/CLIENT/SECRET/COOKIE_SECRET; ensure IdP emits 'groups'
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.auth-rbac.yml up -d reverse-proxy oauth2-proxy
open http://localhost:8081
```

## Groups → Tenant & Role
- Expected groups: `tenant_<id>`, and one or more of `role_admin|role_reviewer|role_user`.
- Nginx sets headers: `X-User`, `X-Email`, `X-Groups`, `X-Tenant-Id` (extracted from groups).

## Enforcement
- Proxy-level hard gates:
  - Admin-only: `/v2/quotas`, `/v1/engagements/{id}/plan`
  - Admin or reviewer: `/v2/approvals`
- OPA-level: use `policies/policy.v4.rego` to gate actions like `start_run`, `approve`, `view_report`, risk tiers, and intrusive runs.

> This overlay is additive and does not modify your backend. When ready, disable any dev header bypass in production and rely solely on the proxy headers.
