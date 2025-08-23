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
