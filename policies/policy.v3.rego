package pentest.policy

default allow = false

# Guards
tenant_ok { input.user.tenant_id == input.tenant_id }

# Risk tier gates
is_safe_passive { input.plan.risk_tier == "safe_passive" }
is_safe_active { input.plan.risk_tier == "safe_active" }
is_intrusive   { input.plan.risk_tier == "intrusive" }

# Active adapters allowed only on safe_active or above
active_adapter {
  some s
  s := input.plan.steps[_]
  s.id == "web_zap_baseline"  # baseline
} or_active_adapter {
  some s
  s := input.plan.steps[_]
  s.id == "web_nuclei_default"
}

approver {
  some r
  r := input.user.roles[_]
  r == "admin" or r == "approver"
}

# Quotas sanity if provided
quota_ok { not input.quota } else_quota_ok {
  input.quota.per_plan_cap >= 1
  input.quota.monthly_budget >= input.quota.per_plan_cap
}

# Create plan policy
allow {
  tenant_ok
  quota_ok
  is_safe_passive
  input.action == "create_plan"
}

allow {
  tenant_ok
  quota_ok
  is_safe_active
  input.action == "create_plan"
  # If using 'active' adapters, still safe on 'safe_active'
}

# Start run policy
allow {
  tenant_ok
  is_safe_passive
  input.action == "start_run"
}

allow {
  tenant_ok
  is_safe_active
  input.action == "start_run"
}

# Intrusive requires approval + approver role
allow {
  tenant_ok
  is_intrusive
  approver
  input.approval == true
  input.action == "start_run"
}
