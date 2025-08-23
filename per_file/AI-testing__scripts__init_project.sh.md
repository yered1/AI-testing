# File: AI-testing/scripts/init_project.sh

- Size: 12070 bytes
- Kind: text
- SHA256: b21c59e86c530b6ad5da7ae49b5c7fcb874a73cdc7579f839f707295a9146d25

## Head (first 60 lines)

```
#!/bin/bash
# Initialize the AI-testing project with all necessary files

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "========================================"
echo "Initializing AI Pentest Platform"
echo "========================================"

# 1. Create directory structure
echo "Creating directory structure..."
mkdir -p "${PROJECT_ROOT}/orchestrator/catalog/tests"
mkdir -p "${PROJECT_ROOT}/orchestrator/catalog/packs"
mkdir -p "${PROJECT_ROOT}/orchestrator/routers"
mkdir -p "${PROJECT_ROOT}/orchestrator/brain/providers"
mkdir -p "${PROJECT_ROOT}/orchestrator/alembic/versions"
mkdir -p "${PROJECT_ROOT}/orchestrator/models"
mkdir -p "${PROJECT_ROOT}/orchestrator/agent_sdk"
mkdir -p "${PROJECT_ROOT}/policies"
mkdir -p "${PROJECT_ROOT}/agents/dev_agent"
mkdir -p "${PROJECT_ROOT}/infra"

# 2. Create catalog files if they don't exist
if [ ! -f "${PROJECT_ROOT}/orchestrator/catalog/tests/tests.json" ]; then
    echo "Creating catalog files..."
    cat > "${PROJECT_ROOT}/orchestrator/catalog/tests/tests.json" << 'EOF'
{
  "network_scan": {
    "id": "network_scan",
    "name": "Network Scan",
    "description": "Basic network scanning",
    "category": "Network",
    "agent_type": "network",
    "risk_level": "low",
    "requires_approval": false
  },
  "web_scan": {
    "id": "web_scan",
    "name": "Web Application Scan",
    "description": "Web application scanning",
    "category": "Web",
    "agent_type": "web",
    "risk_level": "low",
    "requires_approval": false
  }
}
EOF

    cat > "${PROJECT_ROOT}/orchestrator/catalog/packs/packs.json" << 'EOF'
{
  "basic": {
    "id": "basic",
    "name": "Basic Security Assessment",
    "description": "Basic security testing",
    "tests": ["network_scan", "web_scan"]
  }
}
```

## Tail (last 60 lines)

```
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create runs table
    op.create_table('runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('engagement_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('command', sa.String(), nullable=True),
        sa.Column('params', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('jobs')
    op.drop_table('runs')
    op.drop_table('engagements')
    op.drop_table('agents')
    op.drop_table('tenants')
EOF
fi

# 9. Make scripts executable
chmod +x "${PROJECT_ROOT}/scripts/"*.sh 2>/dev/null || true

echo ""
echo "========================================"
echo "Initialization Complete!"
echo "========================================"
echo ""
echo "Project structure created successfully!"
echo ""
echo "Next steps:"
echo "1. Commit these files to your repository:"
echo "   git add ."
echo "   git commit -m 'fix: Add missing project files and fix CI'"
echo "   git push"
echo ""
echo "2. Start the services locally:"
echo "   docker compose -f infra/docker-compose.v2.yml up -d"
echo ""
echo "3. Run migrations:"
echo "   docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head"
echo ""
echo "The CI should now pass!"
```

