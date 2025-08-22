package pentest.policy

default allow = false

# Allow recon and safe_active by default
allow {
  input.risk_tier == "recon"
}
allow {
  input.risk_tier == "safe_active"
}

deny[msg] {
  input.risk_tier == "intrusive"
  not input.approval_granted
  msg := "intrusive tier requires human approval"
}

deny[msg] {
  not scope_valid
  msg := "scope invalid or out of policy"
}

scope_valid {
  # Very basic example: either domains or cidrs must be present
  count(input.scope.in_scope_domains) > 0 or count(input.scope.in_scope_cidrs) > 0
}
