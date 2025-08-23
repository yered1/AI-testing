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
