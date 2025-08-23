# File: AI-testing/.github/workflows/ci.yml

- Size: 5754 bytes
- Kind: text
- SHA256: c79499450b25d44d9954bec8a22020c64f40b315c89117c63fd9db5fcd276fb7

## Head (first 60 lines)

```
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Create necessary directories
      run: |
        mkdir -p orchestrator/catalog/tests
        mkdir -p orchestrator/catalog/packs
        mkdir -p orchestrator/routers
        mkdir -p orchestrator/alembic/versions
        mkdir -p policies
    
    - name: Create minimal catalog files
      run: |
        echo '{}' > orchestrator/catalog/tests/tests.json
        echo '{}' > orchestrator/catalog/packs/packs.json
    
    - name: Create minimal policy file
      run: |
        cat > policies/policy.rego << 'EOF'
        package authz
        default allow = true
        EOF
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Create Docker network
      run: docker network create ai-testing-net || true
    
    - name: Start services
      run: |
        # Start services using docker-compose v2
        docker compose -f infra/docker-compose.v2.yml up -d db opa
        
        # Wait for PostgreSQL
        echo "Waiting for PostgreSQL..."
        for i in {1..30}; do
          if docker compose -f infra/docker-compose.v2.yml exec -T db pg_isready -U pentest 2>/dev/null; then
            echo "PostgreSQL is ready"
            break
          fi
          echo "Waiting for PostgreSQL... ($i/30)"
          sleep 2
```

## Tail (last 60 lines)

```
        def test_health():
            resp = requests.get("http://localhost:8080/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "healthy"
        
        def test_catalog():
            headers = {
                "X-Dev-User": "ci",
                "X-Dev-Email": "ci@test.com",
                "X-Tenant-Id": "t_demo"
            }
            resp = requests.get("http://localhost:8080/v1/catalog", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert "tests" in data
        
        def test_agent_token():
            headers = {
                "Content-Type": "application/json",
                "X-Dev-User": "ci",
                "X-Dev-Email": "ci@test.com",
                "X-Tenant-Id": "t_demo"
            }
            data = {"tenant_id": "t_demo", "name": "test-agent"}
            resp = requests.post("http://localhost:8080/v2/agent_tokens", 
                                headers=headers, 
                                json=data)
            assert resp.status_code == 200
            assert "token" in resp.json()
        
        if __name__ == "__main__":
            test_health()
            print("✓ Health check passed")
            test_catalog()
            print("✓ Catalog check passed")
            test_agent_token()
            print("✓ Agent token check passed")
            print("\nAll tests passed!")
        EOF
        
        # Run the test
        python test_smoke.py
    
    - name: Collect logs on failure
      if: failure()
      run: |
        echo "=== Orchestrator Logs ==="
        docker compose -f infra/docker-compose.v2.yml logs orchestrator || true
        echo "=== Database Logs ==="
        docker compose -f infra/docker-compose.v2.yml logs db || true
        echo "=== OPA Logs ==="
        docker compose -f infra/docker-compose.v2.yml logs opa || true
        echo "=== Docker PS ==="
        docker ps -a
    
    - name: Cleanup
      if: always()
      run: |
        docker compose -f infra/docker-compose.v2.yml down -v || true
        docker network rm ai-testing-net || true
```

