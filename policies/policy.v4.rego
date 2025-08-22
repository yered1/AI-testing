package pentest.policy

default allow = false

# Expect input:
# input.user: { email, groups, tenant_id }
# input.action: "create_plan" | "start_run" | "set_quota" | "approve" | "view_report" ...
# input.request: { path, method, tenant_id }
# input.approval: bool
# input.plan.risk_tier: "safe_passive" | "safe_active" | "intrusive"

tenant_ok { input.user.tenant_id == input.request.tenant_id }

has_role(r) {
  some g
  g := input.user.groups[_]
  g == r
}

is_admin     { has_role("role_admin") }
is_reviewer  { has_role("role_reviewer") }
is_user      { has_role("role_user") }

# Risk tiers
safe_passive { input.plan.risk_tier == "safe_passive" }
safe_active  { input.plan.risk_tier == "safe_active" }
intrusive    { input.plan.risk_tier == "intrusive" }

# Admin: most actions in-tenant
allow {
  tenant_ok
  is_admin
}

# Reviewer: approvals + view reports
allow {
  tenant_ok
  is_reviewer
  input.action == "approve"
}
allow {
  tenant_ok
  is_reviewer
  input.action == "view_report"
}

# User: start runs, view results
allow {
  tenant_ok
  is_user
  input.action == "start_run"
}
allow {
  tenant_ok
  is_user
  input.action == "view_result"
}

# Intrusive requires admin + approval
allow {
  tenant_ok
  intrusive
  is_admin
  input.approval == true
}
