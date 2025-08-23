# File: AI-testing/policies/policy.rego

- Size: 339 bytes
- Kind: text
- SHA256: 8d295357d61afd8c591472fc91ac95efe67a8191951d7b4bf6b8e22e9fef28c8

## Head (first 60 lines)

```
package ai_testing

default allow = false

# Allow read operations
allow {
    input.method == "GET"
}

# Allow authenticated writes
allow {
    input.method == "POST"
    input.user.id != null
}

# Deny scanning private IPs without approval
deny {
    input.action == "scan"
    input.target_private == true
    input.approved == false
}
```

