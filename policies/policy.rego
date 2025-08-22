package pentest.policy

default allow = false

allow {
  input.risk_tier == "recon"
}
allow {
  input.risk_tier == "safe_active"
}

deny[msg] {
  input.risk_tier == "intrusive"
  msg := "intrusive tier requires human approval"
}

deny[msg] {
  not scope_valid
  msg := "scope invalid or out of policy"
}

scope_valid {
  count(input.scope.in_scope_domains) > 0  # stub example
}
