#!/bin/bash
# Destination: patches/v2.0.0/scripts/ci_stack.sh
# Rationale: Orchestrate the full stack startup for CI/CD
# Handles building, migrations, and service startup in correct order

set -e

# Configuration
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-orchestrator}
COMPOSE_FILES="-f docker-compose.yml"
NETWORK_NAME="${COMPOSE_PROJECT_NAME}_network"

# Add OPA compatibility if exists
if [ -f "docker-compose.opa.compat.yml" ]; then
    COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.opa.compat.yml"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Stack startup failed. Printing logs..."
        docker-compose $COMPOSE_FILES logs --tail=100
    fi
    exit $exit_code
}

trap cleanup EXIT

# Create network if it doesn't exist
create_network() {
    log_step "Creating Docker network..."
    if docker network inspect $NETWORK_NAME >/dev/null 2>&1; then
        log_info "Network $NETWORK_NAME already exists"
    else
        docker network create $NETWORK_NAME
        log_info "Created network $NETWORK_NAME"
    fi
}

# Build services
build_services() {
    log_step "Building services..."
    docker-compose $COMPOSE_FILES build --parallel
    log_info "✅ Services built successfully"
}

# Start infrastructure services
start_infrastructure() {
    log_step "Starting infrastructure services (DB, OPA, Redis)..."
    
    # Start database first
    docker-compose $COMPOSE_FILES up -d postgres
    
    # Wait for database to be healthy
    log_info "Waiting for database to be ready..."
    local max_wait=60
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if docker-compose $COMPOSE_FILES exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
            log_info "✅ Database is ready"
            break
        fi
        sleep 2
        waited=$((waited + 2))
        echo -n "."
    done
    echo ""
    
    if [ $waited -ge $max_wait ]; then
        log_error "Database failed to become ready"
        exit 1
    fi
    
    # Start other infrastructure services
    docker-compose $COMPOSE_FILES up -d redis opa
    log_info "✅ Infrastructure services started"
}

# Run database migrations
run_migrations() {
    log_step "Running database migrations..."
    
    # Build migration container with current code
    docker-compose $COMPOSE_FILES build orchestrator
    
    # Run migrations using the orchestrator container
    docker-compose $COMPOSE_FILES run --rm \
        -e PYTHONPATH=/app \
        -w /app/orchestrator \
        orchestrator \
        alembic upgrade head
    
    if [ $? -eq 0 ]; then
        log_info "✅ Migrations completed successfully"
    else
        log_error "Migration failed"
        exit 1
    fi
}

# Start application services
start_applications() {
    log_step "Starting application services..."
    
    # Start orchestrator API
    docker-compose $COMPOSE_FILES up -d orchestrator
    
    # Start agents if they exist
    for agent in kali_agent remote_agent cloud_agent; do
        if docker-compose $COMPOSE_FILES config --services | grep -q $agent; then
            log_info "Starting $agent..."
            docker-compose $COMPOSE_FILES up -d $agent
        fi
    done
    
    # Start reporter service if exists
    if docker-compose $COMPOSE_FILES config --services | grep -q reporter; then
        docker-compose $COMPOSE_FILES up -d reporter
    fi
    
    # Start UI if exists
    if docker-compose $COMPOSE_FILES config --services | grep -q ui; then
        docker-compose $COMPOSE_FILES up -d ui
    fi
    
    log_info "✅ Application services started"
}

# Wait for services to be healthy
wait_for_health() {
    log_step "Waiting for services to be healthy..."
    
    # Wait for orchestrator API
    log_info "Checking orchestrator API health..."
    local api_url="http://localhost:8000/health"
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s $api_url >/dev/null 2>&1; then
            log_info "✅ Orchestrator API is healthy"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
        echo -n "."
    done
    echo ""
    
    if [ $attempt -ge $max_attempts ]; then
        log_error "Orchestrator API failed to become healthy"
        exit 1
    fi
    
    # Check OPA if it's running
    if docker-compose $COMPOSE_FILES ps | grep -q opa; then
        log_info "Checking OPA health..."
        if curl -f -s http://localhost:8181/health >/dev/null 2>&1; then
            log_info "✅ OPA is healthy"
        else
            log_warning "OPA health check failed (non-critical)"
        fi
    fi
}

# Show service status
show_status() {
    log_step "Service Status:"
    docker-compose $COMPOSE_FILES ps
    
    echo ""
    log_info "🎉 Stack is up and running!"
    log_info "📍 API: http://localhost:8000"
    log_info "📍 UI: http://localhost:3000"
    log_info "📍 OPA: http://localhost:8181"
    echo ""
}

# Main execution
main() {
    log_info "🚀 Starting CI/CD stack..."
    
    # Change to project root
    if [ -f "../docker-compose.yml" ]; then
        cd ..
    fi
    
    # Verify we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml not found. Please run from project root."
        exit 1
    fi
    
    # Execute startup sequence
    create_network
    build_services
    start_infrastructure
    run_migrations
    start_applications
    wait_for_health
    show_status
    
    log_info "✅ CI/CD stack startup completed successfully!"
}

# Parse arguments
case "${1:-}" in
    down)
        log_info "Shutting down stack..."
        docker-compose $COMPOSE_FILES down
        ;;
    restart)
        log_info "Restarting stack..."
        docker-compose $COMPOSE_FILES down
        main
        ;;
    logs)
        docker-compose $COMPOSE_FILES logs -f ${2:-}
        ;;
    *)
        main
        ;;
esac