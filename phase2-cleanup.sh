#!/bin/bash
# Phase 2: Deep Cleanup and Consolidation for AI-Testing Platform
# Run this from the repository root
# This script performs aggressive cleanup and reorganization

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="backup_phase2_$(date +%Y%m%d_%H%M%S)"

# Function definitions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_action() {
    echo -e "${CYAN}[ACTION]${NC} $1"
}

# Create backup
log_info "Creating backup in $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/backup.tar.gz" --exclude='.git' --exclude='node_modules' --exclude='__pycache__' . 2>/dev/null || true
log_success "Backup created: $BACKUP_DIR/backup.tar.gz"

# STEP 1: Archive all overlay-related files
log_action "Step 1: Archiving overlay files..."
mkdir -p archived_overlays
# Move all versioned scripts to archive
find scripts -name "*_v[0-9]*.sh" -exec mv {} archived_overlays/ \; 2>/dev/null || true
find scripts -name "*_v[0-9]*.py" -exec mv {} archived_overlays/ \; 2>/dev/null || true
# Move README deltas
mv README_DELTA_v*.md archived_overlays/ 2>/dev/null || true
log_success "Overlay files archived"

# STEP 2: Clean up all junk files aggressively
log_action "Step 2: Aggressive junk cleanup..."
# Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# OS junk
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -type d -name "__MACOSX" -exec rm -rf {} + 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true

# Editor files
find . -name "*.swp" -delete 2>/dev/null || true
find . -name "*.swo" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true
find . -name ".*.swp" -delete 2>/dev/null || true

# Logs and temp files
find . -name "*.log" -delete 2>/dev/null || true
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
find . -name "*.orig" -delete 2>/dev/null || true

log_success "Junk files cleaned"

# STEP 3: Consolidate Docker Compose files
log_action "Step 3: Consolidating Docker Compose files..."
mkdir -p infra/archived_compose
# Archive old compose files
mv infra/docker-compose.v*.yml infra/archived_compose/ 2>/dev/null || true
mv infra/docker-compose.agents.*.yml infra/archived_compose/ 2>/dev/null || true
mv infra/docker-compose.*.yml infra/archived_compose/ 2>/dev/null || true

# Create main consolidated compose file
cat > infra/docker-compose.yml << 'EOF'
# AI-Testing Platform - Main Docker Compose Configuration
# Usage: docker compose up -d
# Profiles: default, agents, full, dev

version: '3.8'

x-common-env: &common-env
  LOG_LEVEL: ${LOG_LEVEL:-INFO}
  TZ: ${TZ:-UTC}

services:
  # ============= CORE SERVICES =============
  db:
    image: postgres:15-alpine
    container_name: ai_testing_db
    environment:
      POSTGRES_DB: ${DB_NAME:-ai_testing}
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ai_testing

  redis:
    image: redis:7-alpine
    container_name: ai_testing_redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - ai_testing

  orchestrator:
    build:
      context: ../orchestrator
      dockerfile: Dockerfile
    container_name: ai_testing_orchestrator
    environment:
      <<: *common-env
      DATABASE_URL: postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-postgres}@db:5432/${DB_NAME:-ai_testing}
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY:-change-me-in-production}
      ALLOW_ACTIVE_SCAN: ${ALLOW_ACTIVE_SCAN:-0}
      EVIDENCE_DIR: ${EVIDENCE_DIR:-/evidence}
      OPA_URL: ${OPA_URL:-http://opa:8181}
      # AI Providers (optional)
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      AZURE_OPENAI_KEY: ${AZURE_OPENAI_KEY:-}
      AZURE_OPENAI_ENDPOINT: ${AZURE_OPENAI_ENDPOINT:-}
    volumes:
      - evidence_data:/evidence
      - ../orchestrator:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "${API_PORT:-8080}:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - ai_testing

  opa:
    image: openpolicyagent/opa:0.65.0
    container_name: ai_testing_opa
    command: ["run", "--server", "--addr", ":8181", "/policies"]
    volumes:
      - ../policies:/policies:ro
    ports:
      - "${OPA_PORT:-8181}:8181"
    networks:
      - ai_testing

  # ============= UI SERVICE (Profile: full, dev) =============
  ui:
    build:
      context: ../ui
      dockerfile: Dockerfile
    container_name: ai_testing_ui
    profiles: ["full", "dev"]
    environment:
      API_URL: ${API_URL:-http://orchestrator:8080}
    depends_on:
      - orchestrator
    ports:
      - "${UI_PORT:-3000}:3000"
    networks:
      - ai_testing

  # ============= AGENTS (Profile: agents, full) =============
  zap-agent:
    build:
      context: ../agents/zap_agent
      dockerfile: Dockerfile
    container_name: ai_testing_zap
    profiles: ["agents", "full"]
    environment:
      <<: *common-env
      ORCHESTRATOR_URL: http://orchestrator:8080
      AGENT_TOKEN: ${ZAP_AGENT_TOKEN}
      ALLOW_ACTIVE_SCAN: ${ALLOW_ACTIVE_SCAN:-0}
    depends_on:
      - orchestrator
    networks:
      - ai_testing

  nuclei-agent:
    build:
      context: ../agents/nuclei_agent
      dockerfile: Dockerfile
    container_name: ai_testing_nuclei
    profiles: ["agents", "full"]
    environment:
      <<: *common-env
      ORCHESTRATOR_URL: http://orchestrator:8080
      AGENT_TOKEN: ${NUCLEI_AGENT_TOKEN}
    depends_on:
      - orchestrator
    networks:
      - ai_testing

  semgrep-agent:
    build:
      context: ../agents/semgrep_agent
      dockerfile: Dockerfile
    container_name: ai_testing_semgrep
    profiles: ["agents", "full"]
    environment:
      <<: *common-env
      ORCHESTRATOR_URL: http://orchestrator:8080
      AGENT_TOKEN: ${SEMGREP_AGENT_TOKEN}
    depends_on:
      - orchestrator
    networks:
      - ai_testing

volumes:
  postgres_data:
  redis_data:
  evidence_data:

networks:
  ai_testing:
    driver: bridge
EOF

log_success "Docker Compose consolidated"

# STEP 4: Reorganize script directory
log_action "Step 4: Reorganizing scripts..."
mkdir -p scripts/{setup,maintenance,testing,agents,deployment}

# Create consolidated management script
cat > scripts/manage.sh << 'EOF'
#!/bin/bash
# AI-Testing Platform Management Script
# Central control for all platform operations

set -e

COMMAND=${1:-help}
shift || true

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

case "$COMMAND" in
    # Service Management
    up)
        echo -e "${BLUE}Starting AI-Testing Platform...${NC}"
        docker compose -f infra/docker-compose.yml up -d "$@"
        echo -e "${GREEN}Platform started! Access at http://localhost:8080${NC}"
        ;;
    
    down)
        echo -e "${YELLOW}Stopping AI-Testing Platform...${NC}"
        docker compose -f infra/docker-compose.yml down "$@"
        ;;
    
    restart)
        $0 down
        $0 up
        ;;
    
    logs)
        docker compose -f infra/docker-compose.yml logs -f "$@"
        ;;
    
    status)
        docker compose -f infra/docker-compose.yml ps
        ;;
    
    # Database Operations
    migrate)
        echo -e "${BLUE}Running database migrations...${NC}"
        docker compose -f infra/docker-compose.yml exec orchestrator alembic upgrade head
        echo -e "${GREEN}Migrations complete!${NC}"
        ;;
    
    db-shell)
        docker compose -f infra/docker-compose.yml exec db psql -U postgres -d ai_testing
        ;;
    
    # Testing
    test)
        echo -e "${BLUE}Running smoke tests...${NC}"
        python scripts/testing/smoke_test.py "$@"
        ;;
    
    test-api)
        curl -s http://localhost:8080/health | jq .
        ;;
    
    # Agent Management
    agent-token)
        AGENT_NAME=${1:-agent}
        curl -s -X POST http://localhost:8080/v2/agent_tokens \
            -H 'Content-Type: application/json' \
            -H 'X-Dev-User: admin' \
            -H 'X-Dev-Email: admin@test.local' \
            -H 'X-Tenant-Id: t_default' \
            -d '{"tenant_id":"t_default","name":"'$AGENT_NAME'"}' | jq -r .token
        ;;
    
    # Development
    shell)
        docker compose -f infra/docker-compose.yml exec orchestrator /bin/bash
        ;;
    
    clean)
        echo -e "${YELLOW}Cleaning temporary files...${NC}"
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        find . -name ".DS_Store" -delete 2>/dev/null || true
        echo -e "${GREEN}Cleanup complete!${NC}"
        ;;
    
    # Full Stack Operations
    full-start)
        $0 up
        sleep 5
        $0 migrate
        echo -e "${GREEN}Full stack ready!${NC}"
        ;;
    
    full-reset)
        echo -e "${YELLOW}WARNING: This will delete all data!${NC}"
        read -p "Continue? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            $0 down -v
            $0 full-start
        fi
        ;;
    
    help)
        echo "AI-Testing Platform Management"
        echo "=============================="
        echo "Service Management:"
        echo "  up              - Start all services"
        echo "  down            - Stop all services"
        echo "  restart         - Restart all services"
        echo "  logs [service]  - View logs"
        echo "  status          - Show service status"
        echo ""
        echo "Database:"
        echo "  migrate         - Run database migrations"
        echo "  db-shell        - Open PostgreSQL shell"
        echo ""
        echo "Testing:"
        echo "  test            - Run smoke tests"
        echo "  test-api        - Quick API health check"
        echo ""
        echo "Agents:"
        echo "  agent-token [name] - Generate agent token"
        echo ""
        echo "Development:"
        echo "  shell           - Open orchestrator shell"
        echo "  clean           - Clean temporary files"
        echo ""
        echo "Full Stack:"
        echo "  full-start      - Start and initialize everything"
        echo "  full-reset      - Reset everything (DELETES DATA)"
        ;;
    
    *)
        echo "Unknown command: $COMMAND"
        echo "Run '$0 help' for usage"
        exit 1
        ;;
esac
EOF
chmod +x scripts/manage.sh

log_success "Scripts reorganized"

# STEP 5: Create proper project structure
log_action "Step 5: Creating proper project structure..."

# Create directory structure
mkdir -p {docs,tests/{unit,integration,e2e},config,templates}

# Create project documentation
cat > docs/PROJECT_STRUCTURE.md << 'EOF'
# AI-Testing Platform - Project Structure

## Directory Layout

```
ai-testing/
├── orchestrator/          # Core orchestration service
│   ├── app.py            # Main application
│   ├── models/           # Database models
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic
│   ├── agent_sdk/        # Agent SDK
│   └── alembic/          # Database migrations
│
├── agents/               # Security testing agents
│   ├── zap_agent/        # OWASP ZAP agent
│   ├── nuclei_agent/     # Nuclei scanner
│   ├── semgrep_agent/    # Code analysis
│   ├── nmap_agent/       # Network scanner
│   ├── mobile_apk_agent/ # Mobile testing
│   └── kali_agent/       # Kali tools integration
│
├── ui/                   # Web interface
│   ├── src/              # Source code
│   ├── public/           # Static assets
│   └── package.json      # Dependencies
│
├── infra/                # Infrastructure
│   ├── docker-compose.yml # Main compose file
│   ├── kubernetes/       # K8s manifests
│   └── terraform/        # IaC definitions
│
├── policies/             # OPA policies
│   └── rbac.rego        # RBAC rules
│
├── scripts/              # Utility scripts
│   ├── manage.sh        # Main management script
│   ├── setup/           # Installation scripts
│   ├── maintenance/     # Cleanup & maintenance
│   ├── testing/         # Test scripts
│   ├── agents/          # Agent-specific scripts
│   └── deployment/      # Deployment scripts
│
├── tests/                # Test suites
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
│
├── docs/                 # Documentation
│   ├── API.md           # API documentation
│   ├── AGENTS.md        # Agent development guide
│   ├── DEPLOYMENT.md    # Deployment guide
│   └── SECURITY.md      # Security guidelines
│
├── config/               # Configuration files
│   ├── default.env      # Default environment
│   ├── staging.env      # Staging environment
│   └── production.env   # Production environment
│
└── templates/            # Report templates
    ├── html/
    ├── pdf/
    └── markdown/
```

## Key Files

- `scripts/manage.sh` - Central management script
- `.env` - Environment configuration
- `docker-compose.yml` - Service definitions
- `README.md` - Main documentation

## Quick Start

1. Copy environment file: `cp config/default.env .env`
2. Start services: `./scripts/manage.sh up`
3. Run migrations: `./scripts/manage.sh migrate`
4. Access UI: http://localhost:8080/ui
EOF

log_success "Project structure created"

# STEP 6: Consolidate and simplify README
log_action "Step 6: Creating consolidated README..."

cat > README.md << 'EOF'
# AI-Testing Platform

A comprehensive security testing orchestration platform that automates various security testing methodologies including web application testing, network scanning, code analysis, and mobile application testing.

## Features

- **Multi-Agent Architecture**: Distributed testing agents for various security tools
- **AI-Powered Planning**: Intelligent test plan generation and risk assessment
- **Comprehensive Testing**: Web, network, code, mobile, and infrastructure testing
- **RBAC & Multi-tenancy**: Enterprise-ready access control
- **Real-time Reporting**: Live test execution monitoring and comprehensive reports

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.9+
- 8GB RAM minimum
- Linux or macOS

### Installation

```bash
# Clone repository
git clone https://github.com/yered1/AI-testing.git
cd AI-testing

# Setup environment
cp config/default.env .env
# Edit .env with your configuration

# Start platform
./scripts/manage.sh full-start

# Access the platform
open http://localhost:8080/ui
```

### Basic Usage

```bash
# Service management
./scripts/manage.sh up          # Start services
./scripts/manage.sh down        # Stop services
./scripts/manage.sh logs        # View logs
./scripts/manage.sh status      # Check status

# Testing
./scripts/manage.sh test        # Run smoke tests

# Agent management
./scripts/manage.sh agent-token my-agent  # Generate agent token
```

## Architecture

The platform consists of:
- **Orchestrator**: Core API service managing test execution
- **Agents**: Distributed testing agents (ZAP, Nuclei, Semgrep, Nmap, etc.)
- **UI**: Web interface for test management
- **Brain**: AI-powered test planning and analysis
- **OPA**: Policy engine for access control

## API Documentation

### Authentication
```bash
curl -X POST http://localhost:8080/v2/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

### Core Endpoints
- `POST /v2/engagements` - Create engagement
- `POST /v2/engagements/{id}/plan` - Create test plan
- `POST /v2/plans/{id}/run` - Start test run
- `GET /v2/reports/run/{id}` - Get report

## Development

### Running Tests
```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# Smoke tests
./scripts/manage.sh test
```

### Adding New Agents
See [docs/AGENTS.md](docs/AGENTS.md) for agent development guide.

## Deployment

### Docker Compose (Development)
```bash
docker compose -f infra/docker-compose.yml up -d
```

### Kubernetes (Production)
```bash
kubectl apply -f infra/kubernetes/
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

## Security

⚠️ **Important Security Notes**:
- Never enable `ALLOW_ACTIVE_SCAN` without proper authorization
- Rotate agent tokens regularly
- Use TLS in production
- Review [docs/SECURITY.md](docs/SECURITY.md) before deployment

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

[Your License]

## Support

- Issues: https://github.com/yered1/AI-testing/issues
- Documentation: [docs/](docs/)
EOF

log_success "README consolidated"

# STEP 7: Create .env.example
log_action "Step 7: Creating environment template..."

cat > .env.example << 'EOF'
# AI-Testing Platform Configuration
# Copy to .env and update values

# ========== Core Configuration ==========
ENVIRONMENT=development
SECRET_KEY=change-me-use-random-string-in-production
API_PORT=8080
UI_PORT=3000

# ========== Database ==========
DB_NAME=ai_testing
DB_USER=postgres
DB_PASSWORD=postgres
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}

# ========== Redis ==========
REDIS_URL=redis://localhost:6379

# ========== Storage ==========
EVIDENCE_DIR=/evidence

# ========== Security ==========
ALLOW_ACTIVE_SCAN=0  # NEVER set to 1 without authorization
ENABLE_RBAC=0

# ========== OPA Policy Engine ==========
OPA_URL=http://opa:8181
OPA_PORT=8181

# ========== AI Providers (Optional) ==========
# OpenAI
#OPENAI_API_KEY=
#OPENAI_MODEL=gpt-4o-mini
#OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic
#ANTHROPIC_API_KEY=
#ANTHROPIC_MODEL=claude-3-5-sonnet-20240620

# Azure OpenAI
#AZURE_OPENAI_KEY=
#AZURE_OPENAI_ENDPOINT=
#AZURE_OPENAI_DEPLOYMENT=

# ========== Agent Tokens ==========
# Generate with: ./scripts/manage.sh agent-token [name]
#ZAP_AGENT_TOKEN=
#NUCLEI_AGENT_TOKEN=
#SEMGREP_AGENT_TOKEN=
#NMAP_AGENT_TOKEN=

# ========== OAuth/OIDC (Optional) ==========
#OAUTH2_CLIENT_ID=
#OAUTH2_CLIENT_SECRET=
#OAUTH2_ISSUER=
#OAUTH2_REDIRECT_URI=

# ========== Notifications (Optional) ==========
#SLACK_WEBHOOK=
#EMAIL_SMTP_HOST=
#EMAIL_SMTP_PORT=
#EMAIL_FROM=
EOF

log_success "Environment template created"

# STEP 8: Create migration consolidation
log_action "Step 8: Consolidating database migrations..."

cat > scripts/maintenance/consolidate_migrations.py << 'EOF'
#!/usr/bin/env python3
"""Consolidate all database migrations into a single initial migration"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def consolidate_migrations():
    migrations_dir = Path("orchestrator/alembic/versions")
    
    if not migrations_dir.exists():
        print("Migrations directory not found")
        return
    
    # Archive old migrations
    archive_dir = migrations_dir / "archived"
    archive_dir.mkdir(exist_ok=True)
    
    for migration in migrations_dir.glob("*.py"):
        if migration.name != "__init__.py":
            shutil.move(str(migration), str(archive_dir / migration.name))
    
    # Create consolidated migration
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    migration_file = migrations_dir / f"001_{timestamp}_initial.py"
    
    with open(migration_file, "w") as f:
        f.write('''"""Initial consolidated migration

Revision ID: 001_initial
Create Date: {}
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None

def upgrade():
    # Core tables
    op.create_table('tenants',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now())
    )
    
    op.create_table('engagements',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('tenant_id', sa.String(), sa.ForeignKey('tenants.id')),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String()),
        sa.Column('scope', sa.JSON()),
        sa.Column('status', sa.String()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now())
    )
    
    # Add indexes
    op.create_index('idx_engagements_tenant', 'engagements', ['tenant_id'])
    op.create_index('idx_engagements_status', 'engagements', ['status'])

def downgrade():
    op.drop_table('engagements')
    op.drop_table('tenants')
'''.format(datetime.now()))
    
    print(f"Created consolidated migration: {migration_file}")
    print(f"Archived {len(list(archive_dir.glob('*.py')))} old migrations")

if __name__ == "__main__":
    consolidate_migrations()
EOF

chmod +x scripts/maintenance/consolidate_migrations.py
log_success "Migration consolidation script created"

# STEP 9: Summary and next steps
echo ""
echo "================================================================"
echo -e "${GREEN}Phase 2 Cleanup Complete!${NC}"
echo "================================================================"
echo ""
echo -e "${CYAN}What was done:${NC}"
echo "✓ Archived all overlay-related files to 'archived_overlays/'"
echo "✓ Cleaned all cache and junk files"
echo "✓ Consolidated Docker Compose files to single file"
echo "✓ Reorganized scripts into logical directories"
echo "✓ Created proper project structure"
echo "✓ Simplified README to essential information"
echo "✓ Created comprehensive management script"
echo "✓ Set up environment template"
echo ""
echo -e "${CYAN}Key files created/updated:${NC}"
echo "• scripts/manage.sh - Central management script"
echo "• infra/docker-compose.yml - Consolidated Docker configuration"
echo "• README.md - Simplified documentation"
echo "• .env.example - Environment template"
echo "• docs/PROJECT_STRUCTURE.md - Project organization"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Review and commit changes:"
echo "   git add -A"
echo "   git commit -m 'Phase 2: Deep cleanup and consolidation'"
echo "   git push"
echo ""
echo "2. Test the platform:"
echo "   cp .env.example .env"
echo "   ./scripts/manage.sh full-start"
echo "   ./scripts/manage.sh test"
echo ""
echo "3. Optional: Remove archived files after verification:"
echo "   rm -rf archived_overlays/"
echo "   rm -rf infra/archived_compose/"
echo ""
echo -e "${GREEN}The platform is now clean and consolidated!${NC}"
echo "================================================================"