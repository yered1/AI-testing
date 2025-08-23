# File: AI-testing/scripts/enable_enhanced_features.sh

- Size: 13300 bytes
- Kind: text
- SHA256: d98a8639983774324c0ccfa484bfb2842f04f05625f704f96050c3818e2719bb

## Head (first 60 lines)

```
#!/bin/bash
# Enable enhanced features for AI Pentest Platform
# This script configures all new routers, agents, and features

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "==================================="
echo "AI Pentest Platform Enhancement"
echo "==================================="

# Function to add router to bootstrap if not exists
add_router_to_bootstrap() {
    local router_name=$1
    local router_path=$2
    local bootstrap_file="${PROJECT_ROOT}/orchestrator/bootstrap_extras.py"
    
    if ! grep -q "$router_path" "$bootstrap_file" 2>/dev/null; then
        echo "Adding $router_name to bootstrap..."
        
        # Create backup
        cp "$bootstrap_file" "${bootstrap_file}.bak" 2>/dev/null || true
        
        # Add import if not exists
        if ! grep -q "from .routers import $router_path" "$bootstrap_file" 2>/dev/null; then
            sed -i "/^from .routers import/a from .routers import $router_path" "$bootstrap_file" 2>/dev/null || \
            echo "from .routers import $router_path" >> "$bootstrap_file"
        fi
        
        # Add router mount if not exists
        if ! grep -q "app.include_router($router_path.router)" "$bootstrap_file" 2>/dev/null; then
            sed -i "/app.include_router/a \    app.include_router($router_path.router)" "$bootstrap_file" 2>/dev/null || \
            echo "    app.include_router($router_path.router)" >> "$bootstrap_file"
        fi
    else
        echo "$router_name already in bootstrap"
    fi
}

# 1. Apply database migrations
echo ""
echo "1. Applying database migrations..."
echo "-----------------------------------"
if [ -f "${PROJECT_ROOT}/orchestrator/alembic/versions/0008_findings_enhanced.py" ]; then
    echo "Findings migration ready to apply"
    echo "Run: docker compose exec orchestrator alembic upgrade head"
else
    echo "⚠️  Findings migration not found - create it first"
fi

# 2. Enable new routers
echo ""
echo "2. Enabling enhanced routers..."
echo "--------------------------------"
add_router_to_bootstrap "findings_v2" "findings_v2"

# 3. Update catalog
echo ""
```

## Tail (last 60 lines)

```
# Check Brain providers
echo ""
echo "Testing Brain Providers..."
curl -s -X GET "$API/v3/brain/providers" \
    -H "X-Dev-User: $USER" \
    -H "X-Dev-Email: $EMAIL" \
    -H "X-Tenant-Id: $TENANT" | jq '.' || echo "Brain API not ready"

# Check enhanced catalog
echo ""
echo "Checking Enhanced Catalog..."
curl -s -X GET "$API/v1/catalog" \
    -H "X-Dev-User: $USER" \
    -H "X-Dev-Email: $EMAIL" \
    -H "X-Tenant-Id: $TENANT" | jq '.tests | keys | length' || echo "Catalog not loaded"

echo ""
echo "Smoke test complete!"
EOF

chmod +x "${PROJECT_ROOT}/scripts/smoke_enhanced.sh"
echo "✓ Smoke test script created"

# 9. Final summary
echo ""
echo "==================================="
echo "Enhancement Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Apply database migrations:"
echo "   docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head"
echo ""
echo "2. Copy and configure environment:"
echo "   cp .env.enhanced .env"
echo "   # Edit .env to add API keys and credentials"
echo ""
echo "3. Restart orchestrator to load new features:"
echo "   docker compose -f infra/docker-compose.v2.yml restart orchestrator"
echo ""
echo "4. Create agent tokens and start enhanced agents:"
echo "   # AWS Agent"
echo "   TOKEN=\$(curl -s -X POST $API/v2/agent_tokens ...)"
echo "   AGENT_TOKEN=\$TOKEN bash scripts/agent_aws_up.sh"
echo ""
echo "   # MSF Agent (BE CAREFUL!)"
echo "   TOKEN=\$(curl -s -X POST $API/v2/agent_tokens ...)"
echo "   AGENT_TOKEN=\$TOKEN ALLOW_EXPLOITATION=0 bash scripts/agent_msf_up.sh"
echo ""
echo "5. Run smoke test:"
echo "   bash scripts/smoke_enhanced.sh"
echo ""
echo "==================================="
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "==================================="
echo "- NEVER set ALLOW_EXPLOITATION=1 without written authorization"
echo "- Always use SAFE_MODE=1 for Metasploit agent in production"
echo "- Secure all API keys and credentials properly"
echo "- Review and approve all intrusive tests before running"
echo "==================================="
```

