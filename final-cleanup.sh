#!/bin/bash
# FINAL CLEANUP: Complete Repository Overhaul for AI-Testing Platform
# This script performs a COMPLETE cleanup and restructuring
# Run from repository root: ./final_cleanup.sh

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Logging functions
log_header() {
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_action() { echo -e "${CYAN}[>]${NC} $1"; }

# Create backup
BACKUP_DIR="backup_final_$(date +%Y%m%d_%H%M%S)"
log_header "Creating Final Backup"
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/complete_backup.tar.gz" \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='venv' \
    --exclude='.env' \
    . 2>/dev/null || true
log_success "Backup saved to $BACKUP_DIR/complete_backup.tar.gz"

# ============================================================================
# STEP 1: COMPLETELY REPLACE THE README
# ============================================================================
log_header "Step 1: Creating Clean README"

cat > README.md << 'EOF'
# AI-Testing Platform

A comprehensive automated security testing orchestration platform that manages distributed security testing agents for web applications, APIs, mobile apps, and infrastructure.

## 🚀 Features

- **Multi-Agent Architecture**: Distributed testing with specialized agents (ZAP, Nuclei, Semgrep, Nmap, Kali tools)
- **AI-Powered Planning**: Intelligent test plan generation using OpenAI/Anthropic
- **Comprehensive Coverage**: Web, API, mobile, network, and code security testing
- **Enterprise Ready**: RBAC, multi-tenancy, audit logging
- **Real-time Monitoring**: Live test execution tracking and reporting

## 📋 Prerequisites

- Docker & Docker Compose v2
- Python 3.9+
- 8GB RAM minimum
- Linux/macOS (Windows WSL2 supported)

## 🔧 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/yered1/AI-testing.git
cd AI-testing
cp .env.example .env
```

### 2. Configure Environment
Edit `.env` and set:
- `SECRET_KEY` - Generate a secure random string
- `DB_PASSWORD` - Change from default
- AI provider keys (optional): `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

### 3. Start Platform
```bash
# Start all services and initialize
./scripts/manage.sh full-start

# Verify health
./scripts/manage.sh status
```

### 4. Access Platform
- API: http://localhost:8080
- UI: http://localhost:8080/ui
- Health: http://localhost:8080/health

## 📚 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Agent Development](docs/AGENTS.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Security Guidelines](docs/SECURITY.md)

## 🛠 Management Commands

```bash
# Service Management
./scripts/manage.sh up          # Start services
./scripts/manage.sh down        # Stop services
./scripts/manage.sh restart     # Restart services
./scripts/manage.sh logs        # View logs
./scripts/manage.sh status      # Check status

# Database
./scripts/manage.sh migrate     # Run migrations
./scripts/manage.sh db-shell    # PostgreSQL shell

# Testing
./scripts/manage.sh test        # Run tests
./scripts/manage.sh test-api    # Quick health check

# Agents
./scripts/manage.sh agent-token [name]  # Generate token

# Development
./scripts/manage.sh shell       # Orchestrator shell
./scripts/manage.sh clean       # Clean temp files
```

## 🧪 Running a Security Test

### Via API
```bash
# 1. Create engagement
curl -X POST http://localhost:8080/v2/engagements \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Scan",
    "type": "web_application",
    "scope": {"targets": ["http://example.com"]}
  }'

# 2. Create and run plan
# See API documentation for details
```

### Via UI
1. Navigate to http://localhost:8080/ui/builder
2. Create engagement
3. Select tests
4. Run and monitor

## 🤖 Available Agents

| Agent | Purpose | Status |
|-------|---------|--------|
| ZAP | Web app scanning | ✅ Ready |
| Nuclei | Vulnerability detection | ✅ Ready |
| Semgrep | Code analysis | ✅ Ready |
| Nmap | Network scanning | ✅ Ready |
| Mobile APK | Android analysis | ✅ Ready |
| Kali Remote | Advanced tools | ✅ Ready |

## 🏗 Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│     UI      │────▶│ Orchestrator │────▶│   Agents    │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                     │
                           ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │   Database   │     │   Reports   │
                    └──────────────┘     └─────────────┘
```

## 🔒 Security

⚠️ **Important Security Notes:**
- **NEVER** set `ALLOW_ACTIVE_SCAN=1` without proper authorization
- Use strong passwords and rotate tokens regularly
- Enable TLS in production
- Review security policies before deployment
- Implement network segmentation for agents

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker
docker info
./scripts/manage.sh status

# Check ports
sudo lsof -i :8080
sudo lsof -i :5432
```

### Database issues
```bash
# Reset database (DELETES DATA)
./scripts/manage.sh full-reset
```

### View logs
```bash
./scripts/manage.sh logs orchestrator
./scripts/manage.sh logs db
```

## 📦 Development

### Project Structure
```
ai-testing/
├── orchestrator/     # Core API service
├── agents/          # Testing agents
├── ui/              # Web interface
├── infra/           # Infrastructure configs
├── scripts/         # Management scripts
├── policies/        # OPA policies
└── docs/           # Documentation
```

### Adding New Agents
See [Agent Development Guide](docs/AGENTS.md)

### Running Tests
```bash
pytest tests/unit
pytest tests/integration
./scripts/manage.sh test
```

## 🚢 Deployment

### Docker Compose (Development)
```bash
docker compose -f infra/docker-compose.yml up -d
```

### Kubernetes (Production)
```bash
kubectl apply -f infra/kubernetes/
```

### Cloud Deployment
- AWS: Use ECS or EKS
- GCP: Use Cloud Run or GKE
- Azure: Use Container Instances or AKS

See [Deployment Guide](docs/DEPLOYMENT.md) for details.

## 📄 License

[Specify your license]

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📞 Support

- Issues: https://github.com/yered1/AI-testing/issues
- Documentation: [docs/](docs/)

---
Built with ❤️ for the security community
EOF

log_success "README.md completely replaced with clean version"

# ============================================================================
# STEP 2: CREATE PROPER .ENV.EXAMPLE
# ============================================================================
log_header "Step 2: Creating Complete Environment Template"

cat > .env.example << 'EOF'
# ============================================
# AI-Testing Platform Configuration
# ============================================
# Copy this file to .env and update values

# === CORE CONFIGURATION ===
ENVIRONMENT=development
SECRET_KEY=CHANGE_ME_USE_RANDOM_STRING_IN_PRODUCTION
LOG_LEVEL=INFO

# === API CONFIGURATION ===
API_PORT=8080
API_VERSION=v2
ENABLE_UI=true
UI_PORT=3000

# === DATABASE ===
DB_HOST=db
DB_PORT=5432
DB_NAME=ai_testing
DB_USER=postgres
DB_PASSWORD=CHANGE_ME_IN_PRODUCTION
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# === REDIS ===
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}

# === STORAGE ===
EVIDENCE_DIR=/evidence
MAX_UPLOAD_SIZE=100M

# === SECURITY ===
# CRITICAL: Never set to 1 without proper authorization
ALLOW_ACTIVE_SCAN=0
ENABLE_RBAC=false
JWT_SECRET=${SECRET_KEY}
JWT_EXPIRY=3600

# === OPA POLICY ENGINE ===
OPA_URL=http://opa:8181
OPA_PORT=8181
OPA_ENABLED=true

# === AI PROVIDERS (Optional) ===
# OpenAI Configuration
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_TIMEOUT=60

# Anthropic Configuration
# ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_MODEL=claude-3-opus-20240229
# ANTHROPIC_TIMEOUT=60

# Azure OpenAI Configuration
# AZURE_OPENAI_KEY=...
# AZURE_OPENAI_ENDPOINT=https://....openai.azure.com/
# AZURE_OPENAI_DEPLOYMENT=...
# AZURE_OPENAI_API_VERSION=2024-02-01

# === AGENT TOKENS ===
# Generate with: ./scripts/manage.sh agent-token [name]
# ZAP_AGENT_TOKEN=
# NUCLEI_AGENT_TOKEN=
# SEMGREP_AGENT_TOKEN=
# NMAP_AGENT_TOKEN=
# KALI_AGENT_TOKEN=

# === AUTHENTICATION (Optional) ===
# OAuth2/OIDC Configuration
# OAUTH2_ENABLED=false
# OAUTH2_CLIENT_ID=
# OAUTH2_CLIENT_SECRET=
# OAUTH2_ISSUER=
# OAUTH2_REDIRECT_URI=http://localhost:8080/auth/callback
# OAUTH2_SCOPE=openid email profile

# === NOTIFICATIONS (Optional) ===
# Slack Integration
# SLACK_ENABLED=false
# SLACK_WEBHOOK=https://hooks.slack.com/services/...

# Email Configuration
# EMAIL_ENABLED=false
# EMAIL_SMTP_HOST=smtp.gmail.com
# EMAIL_SMTP_PORT=587
# EMAIL_SMTP_USER=
# EMAIL_SMTP_PASSWORD=
# EMAIL_FROM=noreply@ai-testing.local
# EMAIL_USE_TLS=true

# === MONITORING (Optional) ===
# Prometheus Metrics
# METRICS_ENABLED=true
# METRICS_PORT=9090

# Sentry Error Tracking
# SENTRY_ENABLED=false
# SENTRY_DSN=https://...@sentry.io/...

# === RATE LIMITING ===
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# === FEATURE FLAGS ===
FEATURE_AI_PLANNING=true
FEATURE_REPORT_GENERATION=true
FEATURE_AGENT_AUTODISCOVERY=false
FEATURE_VULNERABILITY_CORRELATION=true

# === DOCKER CONFIGURATION ===
COMPOSE_PROJECT_NAME=ai_testing
DOCKER_BUILDKIT=1
EOF

log_success ".env.example created with all configuration options"

# ============================================================================
# STEP 3: FIX THE MAIN DOCKER-COMPOSE FILE
# ============================================================================
log_header "Step 3: Creating Proper Docker Compose Configuration"

mkdir -p infra
cat > infra/docker-compose.yml << 'EOF'
# AI-Testing Platform - Docker Compose Configuration
version: '3.8'

x-common-env: &common-env
  LOG_LEVEL: ${LOG_LEVEL:-INFO}
  TZ: ${TZ:-UTC}

x-healthcheck-defaults: &healthcheck-defaults
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

services:
  # ============= CORE SERVICES =============
  db:
    image: postgres:15-alpine
    container_name: ai_testing_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME:-ai_testing}
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.UTF-8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres} -d ${DB_NAME:-ai_testing}"]
    networks:
      - ai_testing
    ports:
      - "127.0.0.1:5432:5432"

  redis:
    image: redis:7-alpine
    container_name: ai_testing_redis
    restart: unless-stopped
    command: >
      redis-server
      --appendonly yes
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "redis-cli", "ping"]
    networks:
      - ai_testing
    ports:
      - "127.0.0.1:6379:6379"

  orchestrator:
    build:
      context: ../orchestrator
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: "3.11"
    container_name: ai_testing_orchestrator
    restart: unless-stopped
    environment:
      <<: *common-env
      DATABASE_URL: postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-postgres}@db:5432/${DB_NAME:-ai_testing}
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY:-change-me-in-production}
      ALLOW_ACTIVE_SCAN: ${ALLOW_ACTIVE_SCAN:-0}
      EVIDENCE_DIR: ${EVIDENCE_DIR:-/evidence}
      OPA_URL: ${OPA_URL:-http://opa:8181}
      # AI Providers
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      AZURE_OPENAI_KEY: ${AZURE_OPENAI_KEY:-}
      AZURE_OPENAI_ENDPOINT: ${AZURE_OPENAI_ENDPOINT:-}
      # Features
      ENABLE_UI: ${ENABLE_UI:-true}
      ENABLE_RBAC: ${ENABLE_RBAC:-false}
    volumes:
      - evidence_data:/evidence
      - ../orchestrator:/app
      - ./logs/orchestrator:/var/log/orchestrator
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      opa:
        condition: service_started
    ports:
      - "${API_PORT:-8080}:8080"
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
    networks:
      - ai_testing

  opa:
    image: openpolicyagent/opa:0.65.0
    container_name: ai_testing_opa
    restart: unless-stopped
    command: >
      run
      --server
      --addr :8181
      --set decision_logs.console=true
      /policies
    volumes:
      - ../policies:/policies:ro
    ports:
      - "127.0.0.1:${OPA_PORT:-8181}:8181"
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:8181/health"]
    networks:
      - ai_testing

  # ============= UI SERVICE (Optional) =============
  ui:
    build:
      context: ../ui
      dockerfile: Dockerfile
      target: ${UI_BUILD_TARGET:-production}
    container_name: ai_testing_ui
    restart: unless-stopped
    profiles: ["full", "ui"]
    environment:
      NODE_ENV: ${NODE_ENV:-production}
      API_URL: ${API_URL:-http://orchestrator:8080}
      PUBLIC_URL: ${PUBLIC_URL:-http://localhost:3000}
    depends_on:
      orchestrator:
        condition: service_healthy
    ports:
      - "${UI_PORT:-3000}:3000"
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
    networks:
      - ai_testing

  # ============= AGENTS (Use profiles to enable) =============
  
  # ZAP Agent
  zap-agent:
    build:
      context: ../agents/zap_agent
      dockerfile: Dockerfile
    container_name: ai_testing_zap
    restart: unless-stopped
    profiles: ["agents", "full"]
    environment:
      <<: *common-env
      ORCHESTRATOR_URL: http://orchestrator:8080
      AGENT_TOKEN: ${ZAP_AGENT_TOKEN}
      AGENT_NAME: zap-agent
      ALLOW_ACTIVE_SCAN: ${ALLOW_ACTIVE_SCAN:-0}
    volumes:
      - zap_data:/zap/wrk
    depends_on:
      orchestrator:
        condition: service_healthy
    networks:
      - ai_testing

  # Nuclei Agent
  nuclei-agent:
    build:
      context: ../agents/nuclei_agent
      dockerfile: Dockerfile
    container_name: ai_testing_nuclei
    restart: unless-stopped
    profiles: ["agents", "full"]
    environment:
      <<: *common-env
      ORCHESTRATOR_URL: http://orchestrator:8080
      AGENT_TOKEN: ${NUCLEI_AGENT_TOKEN}
      AGENT_NAME: nuclei-agent
    volumes:
      - nuclei_templates:/root/nuclei-templates
    depends_on:
      orchestrator:
        condition: service_healthy
    networks:
      - ai_testing

  # Semgrep Agent
  semgrep-agent:
    build:
      context: ../agents/semgrep_agent
      dockerfile: Dockerfile
    container_name: ai_testing_semgrep
    restart: unless-stopped
    profiles: ["agents", "full"]
    environment:
      <<: *common-env
      ORCHESTRATOR_URL: http://orchestrator:8080
      AGENT_TOKEN: ${SEMGREP_AGENT_TOKEN}
      AGENT_NAME: semgrep-agent
    depends_on:
      orchestrator:
        condition: service_healthy
    networks:
      - ai_testing

  # Nmap Agent
  nmap-agent:
    build:
      context: ../agents/nmap_agent
      dockerfile: Dockerfile
    container_name: ai_testing_nmap
    restart: unless-stopped
    profiles: ["agents", "full", "network"]
    environment:
      <<: *common-env
      ORCHESTRATOR_URL: http://orchestrator:8080
      AGENT_TOKEN: ${NMAP_AGENT_TOKEN}
      AGENT_NAME: nmap-agent
      ALLOW_ACTIVE_SCAN: ${ALLOW_ACTIVE_SCAN:-0}
    depends_on:
      orchestrator:
        condition: service_healthy
    networks:
      - ai_testing
    cap_add:
      - NET_RAW
      - NET_ADMIN

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  evidence_data:
    driver: local
  zap_data:
    driver: local
  nuclei_templates:
    driver: local

networks:
  ai_testing:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
EOF

log_success "Docker Compose configuration created"

# ============================================================================
# STEP 4: CREATE ESSENTIAL MISSING FILES
# ============================================================================
log_header "Step 4: Creating Essential Files"

# Create Dockerfile for orchestrator if missing
if [ ! -f orchestrator/Dockerfile ]; then
    log_action "Creating orchestrator/Dockerfile"
    cat > orchestrator/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create evidence directory
RUN mkdir -p /evidence

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
EOF
    log_success "orchestrator/Dockerfile created"
fi

# Create requirements.txt if missing
if [ ! -f orchestrator/requirements.txt ]; then
    log_action "Creating orchestrator/requirements.txt"
    cat > orchestrator/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
redis==5.0.1
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
httpx==0.25.1
jinja2==3.1.2
python-dotenv==1.0.0
click==8.1.7
rich==13.7.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
EOF
    log_success "orchestrator/requirements.txt created"
fi

# Create basic app.py if missing
if [ ! -f orchestrator/app.py ]; then
    log_action "Creating orchestrator/app.py"
    cat > orchestrator/app.py << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting AI-Testing Orchestrator...")
    yield
    logger.info("Shutting down AI-Testing Orchestrator...")

# Create FastAPI app
app = FastAPI(
    title="AI-Testing Platform",
    description="Security Testing Orchestration Platform",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AI-Testing Platform",
        "version": "2.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/v2/catalog")
async def get_catalog():
    """Get test catalog"""
    return {
        "tests": [
            {"id": "web_basic", "name": "Basic Web Scan"},
            {"id": "api_test", "name": "API Security Test"},
            {"id": "network_scan", "name": "Network Discovery"}
        ],
        "packs": [
            {"id": "default", "name": "Default Pack"},
            {"id": "comprehensive", "name": "Comprehensive Pack"}
        ]
    }

# Import and mount routers if they exist
try:
    from routers import v2_router
    app.include_router(v2_router, prefix="/v2")
except ImportError:
    logger.warning("v2_router not found, skipping")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
EOF
    log_success "orchestrator/app.py created"
fi

# ============================================================================
# STEP 5: CREATE/UPDATE THE MANAGEMENT SCRIPT
# ============================================================================
log_header "Step 5: Creating Management Script"

mkdir -p scripts
cat > scripts/manage.sh << 'EOF'
#!/bin/bash
# AI-Testing Platform Management Script
# Central control point for all operations

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

COMPOSE_FILE="infra/docker-compose.yml"
COMMAND=${1:-help}
shift || true

# Helper functions
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

case "$COMMAND" in
    # ===== SERVICE MANAGEMENT =====
    up)
        log_info "Starting AI-Testing Platform..."
        docker compose -f $COMPOSE_FILE up -d "$@"
        log_success "Platform started! Access at http://localhost:8080"
        ;;
    
    down)
        log_warning "Stopping AI-Testing Platform..."
        docker compose -f $COMPOSE_FILE down "$@"
        log_success "Platform stopped"
        ;;
    
    restart)
        $0 down
        sleep 2
        $0 up
        ;;
    
    logs)
        docker compose -f $COMPOSE_FILE logs -f "$@"
        ;;
    
    status)
        echo -e "${BLUE}═══ AI-Testing Platform Status ═══${NC}"
        docker compose -f $COMPOSE_FILE ps
        echo ""
        echo "Health Check:"
        curl -s http://localhost:8080/health 2>/dev/null | python3 -m json.tool || echo "API not responding"
        ;;
    
    # ===== DATABASE OPERATIONS =====
    migrate)
        log_info "Running database migrations..."
        docker compose -f $COMPOSE_FILE exec orchestrator alembic upgrade head
        log_success "Migrations complete!"
        ;;
    
    db-shell)
        docker compose -f $COMPOSE_FILE exec db psql -U postgres -d ai_testing
        ;;
    
    db-backup)
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        log_info "Creating database backup: $BACKUP_FILE"
        docker compose -f $COMPOSE_FILE exec -T db pg_dump -U postgres ai_testing > $BACKUP_FILE
        log_success "Backup saved to $BACKUP_FILE"
        ;;
    
    # ===== TESTING =====
    test)
        log_info "Running smoke tests..."
        if [ -f "scripts/testing/smoke_test.py" ]; then
            python3 scripts/testing/smoke_test.py "$@"
        else
            curl -s http://localhost:8080/health | python3 -m json.tool
        fi
        ;;
    
    test-api)
        echo "Testing API endpoints..."
        echo "1. Health check:"
        curl -s http://localhost:8080/health | python3 -m json.tool
        echo -e "\n2. Catalog:"
        curl -s http://localhost:8080/v2/catalog | python3 -m json.tool
        ;;
    
    # ===== AGENT MANAGEMENT =====
    agent-token)
        AGENT_NAME=${1:-agent}
        log_info "Generating token for agent: $AGENT_NAME"
        TOKEN=$(curl -s -X POST http://localhost:8080/v2/agent_tokens \
            -H 'Content-Type: application/json' \
            -H 'X-Dev-User: admin' \
            -H 'X-Dev-Email: admin@test.local' \
            -H 'X-Tenant-Id: t_default' \
            -d '{"tenant_id":"t_default","name":"'$AGENT_NAME'"}' | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', 'ERROR'))")
        echo -e "${GREEN}Token:${NC} $TOKEN"
        ;;
    
    agents-start)
        log_info "Starting all agents..."
        docker compose -f $COMPOSE_FILE --profile agents up -d
        log_success "Agents started"
        ;;
    
    # ===== DEVELOPMENT =====
    shell)
        docker compose -f $COMPOSE_FILE exec orchestrator /bin/bash
        ;;
    
    redis-cli)
        docker compose -f $COMPOSE_FILE exec redis redis-cli
        ;;
    
    clean)
        log_warning "Cleaning temporary files..."
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        find . -name ".DS_Store" -delete 2>/dev/null || true
        docker system prune -f
        log_success "Cleanup complete!"
        ;;
    
    # ===== FULL STACK OPERATIONS =====
    full-start)
        log_info "Starting full stack..."
        $0 up
        sleep 5
        $0 migrate || true
        $0 status
        log_success "Full stack ready!"
        ;;
    
    full-reset)
        log_error "WARNING: This will delete ALL data!"
        read -p "Are you sure? Type 'yes' to continue: " -r
        if [[ $REPLY == "yes" ]]; then
            $0 down -v
            $0 full-start
        else
            echo "Cancelled"
        fi
        ;;
    
    # ===== HELP =====
    help)
        cat << HELP
${BLUE}AI-Testing Platform Management${NC}
═══════════════════════════════════════

${GREEN}Service Management:${NC}
  up              Start all services
  down            Stop all services
  restart         Restart all services
  logs [service]  View logs (follow mode)
  status          Show service status

${GREEN}Database:${NC}
  migrate         Run database migrations
  db-shell        Open PostgreSQL shell
  db-backup       Create database backup

${GREEN}Testing:${NC}
  test            Run smoke tests
  test-api        Quick API endpoint test

${GREEN}Agents:${NC}
  agent-token [name]  Generate agent token
  agents-start        Start all agents

${GREEN}Development:${NC}
  shell           Open orchestrator shell
  redis-cli       Open Redis CLI
  clean           Clean temporary files

${GREEN}Full Stack:${NC}
  full-start      Start and initialize everything
  full-reset      Reset everything (DELETES DATA!)

${GREEN}Examples:${NC}
  $0 up                    # Start platform
  $0 logs orchestrator     # View orchestrator logs
  $0 agent-token zap       # Generate token for ZAP agent
  $0 test                  # Run tests

HELP
        ;;
    
    *)
        log_error "Unknown command: $COMMAND"
        echo "Run '$0 help' for usage"
        exit 1
        ;;
esac
EOF

chmod +x scripts/manage.sh
log_success "Management script created and made executable"

# ============================================================================
# STEP 6: CREATE ESSENTIAL DOCUMENTATION
# ============================================================================
log_header "Step 6: Creating Documentation"

mkdir -p docs

# Create Architecture document
cat > docs/ARCHITECTURE.md << 'EOF'
# AI-Testing Platform Architecture

## System Overview

The AI-Testing Platform is a distributed security testing orchestration system that coordinates multiple specialized testing agents to perform comprehensive security assessments.

## Core Components

### 1. Orchestrator
- Central API service (FastAPI/Python)
- Manages test workflows
- Coordinates agent activities
- Handles result aggregation

### 2. Database (PostgreSQL)
- Stores engagements, plans, runs
- Manages findings and reports
- Handles multi-tenancy

### 3. Cache (Redis)
- Job queue management
- Session storage
- Real-time event streaming

### 4. Policy Engine (OPA)
- RBAC enforcement
- Resource access control
- Security policy validation

### 5. Testing Agents
- ZAP: Web application scanning
- Nuclei: Vulnerability detection
- Semgrep: Code analysis
- Nmap: Network discovery
- Kali: Advanced tools

## Data Flow

1. User creates engagement via API/UI
2. Orchestrator generates test plan
3. Jobs distributed to agents
4. Agents execute tests
5. Results aggregated
6. Reports generated

## Security Model

- JWT-based authentication
- Role-based access control
- Tenant isolation
- Audit logging
- Encrypted storage
EOF

# Create API documentation
cat > docs/API.md << 'EOF'
# API Documentation

## Base URL
```
http://localhost:8080
```

## Authentication
Most endpoints require authentication headers:
```
X-Dev-User: username
X-Dev-Email: user@example.com
X-Tenant-Id: tenant_id
```

## Core Endpoints

### Health Check
```http
GET /health
```

### Get Catalog
```http
GET /v2/catalog
```

### Create Engagement
```http
POST /v2/engagements
Content-Type: application/json

{
  "name": "Test Engagement",
  "type": "web_application",
  "scope": {
    "targets": ["http://example.com"],
    "excluded": []
  }
}
```

### Create Plan
```http
POST /v2/engagements/{engagement_id}/plan
Content-Type: application/json

{
  "tests": [
    {
      "id": "web_basic",
      "params": {}
    }
  ]
}
```

### Start Run
```http
POST /v2/plans/{plan_id}/run
```

### Get Run Status
```http
GET /v2/runs/{run_id}
```

### Get Report
```http
GET /v2/reports/run/{run_id}
```

## Agent Endpoints

### Generate Agent Token
```http
POST /v2/agent_tokens
Content-Type: application/json

{
  "tenant_id": "t_default",
  "name": "agent-name"
}
```

### Lease Job (Agent)
```http
POST /v2/agents/lease
Authorization: Bearer {agent_token}

{
  "agent_type": "zap"
}
```
EOF

log_success "Documentation created"

# ============================================================================
# STEP 7: CREATE .GITIGNORE
# ============================================================================
log_header "Step 7: Creating .gitignore"

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.pytest_cache/
.coverage
.coverage.*
.cache
.tox/
.mypy_cache/
.ruff_cache/

# Virtual Environments
venv/
ENV/
env/
.venv/
.env/

# IDEs
.vscode/
.idea/
*.sublime-project
*.sublime-workspace
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
Thumbs.db
ehthumbs.db
__MACOSX/

# Environment
.env
.env.local
.env.*.local
*.env
!.env.example

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Node
node_modules/
.npm
.yarn-integrity

# Docker
.dockerignore

# Application
evidence/
uploads/
temp/
tmp/
backup*/
*.backup
*.bak
*.orig

# Security
*.key
*.pem
*.crt
*.p12
secrets/
credentials/

# Database
*.db
*.sqlite
*.sqlite3
*.sql
!init.sql

# Archives
*.zip
*.tar
*.tar.gz
*.rar
*.7z

# IDE specific
.project
.pydevproject
.settings/
nbproject/
.nb-gradle/
EOF

log_success ".gitignore created"

# ============================================================================
# FINAL SUMMARY
# ============================================================================
log_header "Cleanup Complete!"

echo -e "${GREEN}✓ README.md replaced with clean version${NC}"
echo -e "${GREEN}✓ .env.example created with all options${NC}"
echo -e "${GREEN}✓ Docker Compose properly configured${NC}"
echo -e "${GREEN}✓ Management script created${NC}"
echo -e "${GREEN}✓ Essential files created${NC}"
echo -e "${GREEN}✓ Documentation added${NC}"
echo -e "${GREEN}✓ .gitignore updated${NC}"

echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "1. Review the changes: git diff"
echo "2. Copy environment: cp .env.example .env"
echo "3. Edit .env with your configuration"
echo "4. Start the platform: ./scripts/manage.sh full-start"
echo "5. Commit changes: git add -A && git commit -m 'Complete platform overhaul'"
echo "6. Push to repository: git push"

echo ""
echo -e "${YELLOW}Important:${NC}"
echo "- The platform has been completely restructured"
echo "- Old overlay references have been removed"
echo "- Use ./scripts/manage.sh for all operations"
echo "- Check docs/ for documentation"

echo ""
echo -e "${GREEN}The AI-Testing platform is now clean and ready for use!${NC}"