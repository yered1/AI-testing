# RBAC via IdP Groups → Tenant & Role

We derive **tenant** and **roles** from the IdP groups claim.
- Tenant: first match of `tenant_<id>` inside groups → becomes `X-Tenant-Id`
- Roles: presence of `role_admin`, `role_reviewer`, `role_user`

Examples:
- Groups: `tenant_acme,role_admin,role_user` → tenant=acme, roles include admin, user
- Groups: `tenant_beta,role_reviewer` → tenant=beta, role=reviewer

Nginx enforces:
- Admin-only: `/v2/quotas`, `/v1/engagements/{id}/plan`
- Admin or Reviewer: `/v2/approvals`
- Authenticated (any role): all others (OPA still enforces deeper rules)

> Adjust regexes in `infra/auth/nginx.rbac.conf` if your IdP uses different naming.
> For Azure AD group GUIDs, consider adding a mapping shim or custom OIDC claim to emit friendly names like `tenant_<id>` and `role_<name>`.
