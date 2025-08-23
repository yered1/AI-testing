package orchestrator.authz

default allow = false

# Allow health checks
allow {
    input.path == ["health"]
}

# Allow all GET requests for now (development)
allow {
    input.method == "GET"
}

# Allow authenticated users
allow {
    input.user.id != ""
}

# Allow API tokens
allow {
    input.headers["X-Agent-Id"] != ""
    input.headers["X-Agent-Key"] != ""
}
