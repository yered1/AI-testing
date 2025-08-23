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
echo "3. Updating test catalog..."
echo "----------------------------"
if [ -f "${PROJECT_ROOT}/orchestrator/catalog/tests/enhanced_tests.json" ]; then
    echo "Merging enhanced tests into catalog..."
    
    # Backup existing catalog
    cp "${PROJECT_ROOT}/orchestrator/catalog/tests/tests.json" \
       "${PROJECT_ROOT}/orchestrator/catalog/tests/tests.json.bak" 2>/dev/null || true
    
    # Merge catalogs (requires jq)
    if command -v jq &> /dev/null; then
        jq -s '.[0] * .[1]' \
            "${PROJECT_ROOT}/orchestrator/catalog/tests/tests.json" \
            "${PROJECT_ROOT}/orchestrator/catalog/tests/enhanced_tests.json" \
            > "${PROJECT_ROOT}/orchestrator/catalog/tests/tests_merged.json"
        mv "${PROJECT_ROOT}/orchestrator/catalog/tests/tests_merged.json" \
           "${PROJECT_ROOT}/orchestrator/catalog/tests/tests.json"
        echo "✓ Enhanced tests merged into catalog"
    else
        echo "⚠️  jq not installed - manually merge enhanced_tests.json into tests.json"
    fi
else
    echo "⚠️  Enhanced tests file not found"
fi

# Merge packs
if [ -f "${PROJECT_ROOT}/orchestrator/catalog/packs/enhanced_packs.json" ]; then
    echo "Merging enhanced packs into catalog..."
    
    # Backup existing packs
    cp "${PROJECT_ROOT}/orchestrator/catalog/packs/packs.json" \
       "${PROJECT_ROOT}/orchestrator/catalog/packs/packs.json.bak" 2>/dev/null || true
    
    if command -v jq &> /dev/null; then
        jq -s '.[0] * .[1]' \
            "${PROJECT_ROOT}/orchestrator/catalog/packs/packs.json" \
            "${PROJECT_ROOT}/orchestrator/catalog/packs/enhanced_packs.json" \
            > "${PROJECT_ROOT}/orchestrator/catalog/packs/packs_merged.json"
        mv "${PROJECT_ROOT}/orchestrator/catalog/packs/packs_merged.json" \
           "${PROJECT_ROOT}/orchestrator/catalog/packs/packs.json"
        echo "✓ Enhanced packs merged into catalog"
    else
        echo "⚠️  jq not installed - manually merge enhanced_packs.json into packs.json"
    fi
else
    echo "⚠️  Enhanced packs file not found"
fi

# 4. Setup agent configurations
echo ""
echo "4. Setting up agent configurations..."
echo "--------------------------------------"

# Create agent compose files
cat > "${PROJECT_ROOT}/infra/docker-compose.agents.enhanced.yml" << 'EOF'
version: '3.8'

services:
  aws_agent:
    build:
      context: ..
      dockerfile: infra/agent.aws.Dockerfile
    environment:
      ORCHESTRATOR_URL: ${ORCHESTRATOR_URL:-http://orchestrator:8080}
      AGENT_TOKEN: ${AWS_AGENT_TOKEN}
      TENANT_ID: ${TENANT_ID:-t_demo}
      ALLOW_ACTIVE_SCAN: ${ALLOW_ACTIVE_SCAN:-0}
      # AWS credentials - set these securely
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      AWS_DEFAULT_REGION: ${AWS_DEFAULT_REGION:-us-east-1}
    networks:
      - ai-testing-net
    restart: unless-stopped

  msf_agent:
    build:
      context: ..
      dockerfile: infra/agent.msf.Dockerfile
    environment:
      ORCHESTRATOR_URL: ${ORCHESTRATOR_URL:-http://orchestrator:8080}
      AGENT_TOKEN: ${MSF_AGENT_TOKEN}
      TENANT_ID: ${TENANT_ID:-t_demo}
      ALLOW_EXPLOITATION: ${ALLOW_EXPLOITATION:-0}
      SAFE_MODE: ${SAFE_MODE:-1}
      MSF_HOST: ${MSF_HOST:-msf}
      MSF_PORT: ${MSF_PORT:-55553}
      MSF_USER: ${MSF_USER:-msf}
      MSF_PASS: ${MSF_PASS:-msf}
      LHOST: ${LHOST:-0.0.0.0}
    networks:
      - ai-testing-net
    depends_on:
      - msf
    restart: unless-stopped

  msf:
    image: metasploitframework/metasploit-framework:latest
    environment:
      MSF_DATABASE_CONFIG: /usr/src/metasploit-framework/config/database.yml
    command: >
      sh -c "msfdb init &&
             msfrpcd -P ${MSF_PASS:-msf} -S -f -a 0.0.0.0 -p 55553"
    networks:
      - ai-testing-net
    volumes:
      - msf_data:/root/.msf4
    restart: unless-stopped

networks:
  ai-testing-net:
    external: true
    name: infra_ai-testing-net

volumes:
  msf_data:
EOF

echo "✓ Enhanced agent compose file created"

# 5. Create agent startup scripts
echo ""
echo "5. Creating agent startup scripts..."
echo "-------------------------------------"

# AWS Agent startup script
cat > "${PROJECT_ROOT}/scripts/agent_aws_up.sh" << 'EOF'
#!/bin/bash
# Start AWS Security Agent

set -e

# Check if token is provided
if [ -z "$AGENT_TOKEN" ]; then
    echo "Error: AGENT_TOKEN not set"
    echo "Usage: AGENT_TOKEN=<token> bash $0"
    exit 1
fi

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$AWS_PROFILE" ]; then
    echo "Warning: No AWS credentials configured"
    echo "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY or AWS_PROFILE"
fi

# Export for docker-compose
export AWS_AGENT_TOKEN="$AGENT_TOKEN"

# Start the agent
echo "Starting AWS Security Agent..."
docker compose -f infra/docker-compose.agents.enhanced.yml up -d aws_agent

echo "AWS Agent started. Tailing logs..."
docker compose -f infra/docker-compose.agents.enhanced.yml logs -f aws_agent
EOF

chmod +x "${PROJECT_ROOT}/scripts/agent_aws_up.sh"
echo "✓ AWS agent startup script created"

# MSF Agent startup script
cat > "${PROJECT_ROOT}/scripts/agent_msf_up.sh" << 'EOF'
#!/bin/bash
# Start Metasploit Agent

set -e

# Check if token is provided
if [ -z "$AGENT_TOKEN" ]; then
    echo "Error: AGENT_TOKEN not set"
    echo "Usage: AGENT_TOKEN=<token> bash $0"
    exit 1
fi

# Safety check
if [ "$ALLOW_EXPLOITATION" == "1" ]; then
    echo "⚠️  WARNING: Exploitation is ENABLED!"
    echo "This agent will attempt to exploit vulnerabilities."
    echo "Only use with proper authorization!"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "Running in SAFE MODE (no actual exploitation)"
fi

# Export for docker-compose
export MSF_AGENT_TOKEN="$AGENT_TOKEN"

# Start MSF and agent
echo "Starting Metasploit Framework and Agent..."
docker compose -f infra/docker-compose.agents.enhanced.yml up -d msf msf_agent

echo "Waiting for MSF to initialize..."
sleep 10

echo "MSF Agent started. Tailing logs..."
docker compose -f infra/docker-compose.agents.enhanced.yml logs -f msf_agent
EOF

chmod +x "${PROJECT_ROOT}/scripts/agent_msf_up.sh"
echo "✓ MSF agent startup script created"

# 6. Update Brain providers
echo ""
echo "6. Configuring AI Brain providers..."
echo "-------------------------------------"

# Check if providers are implemented
if [ -f "${PROJECT_ROOT}/orchestrator/brain/providers/openai_chat.py" ]; then
    echo "✓ OpenAI provider implemented"
    echo "  Set OPENAI_API_KEY to enable"
else
    echo "⚠️  OpenAI provider not found"
fi

if [ -f "${PROJECT_ROOT}/orchestrator/brain/providers/anthropic.py" ]; then
    echo "✓ Anthropic provider implemented"
    echo "  Set ANTHROPIC_API_KEY to enable"
else
    echo "⚠️  Anthropic provider not found"
fi

# 7. Create environment template
echo ""
echo "7. Creating environment template..."
echo "------------------------------------"

cat > "${PROJECT_ROOT}/.env.enhanced" << 'EOF'
# Enhanced AI Pentest Platform Configuration

# Core Settings
ORCHESTRATOR_URL=http://localhost:8080
TENANT_ID=t_demo
EVIDENCE_DIR=/evidence
SIMULATE_PROGRESS=false

# AI Brain Providers
# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-5-sonnet-20240620

# Azure OpenAI
AZURE_OPENAI_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=

# AWS Agent Configuration
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
# Or use AWS_PROFILE=default

# Metasploit Agent Configuration
ALLOW_EXPLOITATION=0  # Set to 1 to enable actual exploitation (DANGEROUS!)
SAFE_MODE=1          # Set to 0 to disable safety checks
MSF_HOST=msf
MSF_PORT=55553
MSF_USER=msf
MSF_PASS=msf
LHOST=0.0.0.0

# Security Settings
ALLOW_ACTIVE_SCAN=0  # Set to 1 for intrusive scans
REQUIRE_APPROVAL=true
MAX_CONCURRENT_JOBS=5

# Notification Settings
SLACK_WEBHOOK_URL=
EMAIL_NOTIFICATIONS=false

# Database
DATABASE_URL=postgresql://pentest:pentest@db:5432/pentest
REDIS_URL=redis://redis:6379

# Auth (if using OIDC)
OIDC_ISSUER=
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
EOF

echo "✓ Enhanced environment template created at .env.enhanced"

# 8. Create comprehensive smoke test
echo ""
echo "8. Creating comprehensive smoke test..."
echo "----------------------------------------"

cat > "${PROJECT_ROOT}/scripts/smoke_enhanced.sh" << 'EOF'
#!/bin/bash
# Comprehensive smoke test for enhanced features

set -e

API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
USER="${USER:-test}"
EMAIL="${EMAIL:-test@example.com}"

echo "==================================="
echo "Enhanced Platform Smoke Test"
echo "==================================="

# Check findings API
echo ""
echo "Testing Findings API..."
curl -s -X GET "$API/v2/findings/stats/test" \
    -H "X-Dev-User: $USER" \
    -H "X-Dev-Email: $EMAIL" \
    -H "X-Tenant-Id: $TENANT" || echo "Findings API not ready"

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