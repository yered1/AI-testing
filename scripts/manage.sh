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
