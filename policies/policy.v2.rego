package pentest.policy

default allow = false

# Inputs expected:
# input.user: { id, email, roles, tenant_id }
# input.action: "create_plan" | "start_run" | "set_quota" | "request_approval" | "approve" ...
# input.plan: { risk_tier: "safe_passive" | "safe_active" | "intrusive", steps: [...] }
# input.quota: { monthly_budget, per_plan_cap }
# input.tenant_id

# Tenant isolation: user must match tenant
tenant_ok {
  input.user.tenant_id == input.tenant_id
}

# Risk policy
risk_ok {
  input.plan.risk_tier == "safe_passive"
} else_risk_ok {
  input.plan.risk_tier == "safe_active"
} else_risk_ok {
  # 'intrusive' requires role approver or admin and approval flag
  input.plan.risk_tier == "intrusive"
  some r
  r := input.user.roles[_]
  r == "admin" or r == "approver"
  input.approval == true
}

# Quota policy
quota_ok {
  not input.quota  # if not provided, skip
} else_quota_ok {
  input.quota.per_plan_cap >= 1
  input.quota.monthly_budget >= input.quota.per_plan_cap
}

allow {
  tenant_ok
  risk_ok
  quota_ok
  input.action == "create_plan"
}

allow {
  tenant_ok
  risk_ok
  input.action == "start_run"
}
