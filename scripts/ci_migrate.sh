#!/bin/bash
# Destination: patches/v2.0.0/scripts/ci_migrate.sh
# Rationale: Run database migrations in CI with proper environment setup
# This script ensures Alembic can find all dependencies and connect to the database

set -e

echo "🔄 Starting database migration process..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check environment variables
check_env_vars() {
    local required_vars=("DATABASE_URL" "POSTGRES_HOST" "POSTGRES_PORT" "POSTGRES_DB" "POSTGRES_USER")
    local found=false
    
    for var in "${required_vars[@]}"; do
        if [ ! -z "${!var}" ]; then
            found=true
            break
        fi
    done
    
    if [ "$found" = false ]; then
        log_error "No database configuration found. Set DATABASE_URL or POSTGRES_* variables."
        exit 1
    fi
}

# Wait for database to be ready
wait_for_db() {
    log_info "Waiting for database to be ready..."
    
    local max_attempts=30
    local attempt=0
    
    # Determine database host and port
    if [ ! -z "$DATABASE_URL" ]; then
        # Extract host and port from DATABASE_URL
        DB_HOST=$(echo $DATABASE_URL | sed -E 's/.*@([^:\/]+).*/\1/')
        DB_PORT=$(echo $DATABASE_URL | sed -E 's/.*:([0-9]+)\/.*/\1/')
    else
        DB_HOST=${POSTGRES_HOST:-localhost}
        DB_PORT=${POSTGRES_PORT:-5432}
    fi
    
    while [ $attempt -lt $max_attempts ]; do
        if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
            log_info "Database is ready at $DB_HOST:$DB_PORT"
            return 0
        fi
        attempt=$((attempt + 1))
        log_warning "Database not ready yet. Attempt $attempt/$max_attempts"
        sleep 2
    done
    
    log_error "Database failed to become ready after $max_attempts attempts"
    exit 1
}

# Run migrations
run_migrations() {
    log_info "Running Alembic migrations..."
    
    # Set Python path to include application root
    export PYTHONPATH="${PYTHONPATH:-}:/app"
    
    # Change to orchestrator directory where alembic.ini is located
    cd /app/orchestrator || {
        log_error "Failed to change to orchestrator directory"
        exit 1
    }
    
    # Check if alembic.ini exists
    if [ ! -f "alembic.ini" ]; then
        log_error "alembic.ini not found in $(pwd)"
        exit 1
    fi
    
    # Check if alembic directory exists
    if [ ! -d "alembic" ]; then
        log_error "alembic directory not found in $(pwd)"
        exit 1
    fi
    
    # Run migration command
    if alembic upgrade head; then
        log_info "✅ Migrations completed successfully"
        return 0
    else
        log_error "Migration failed"
        return 1
    fi
}

# Main execution
main() {
    log_info "Migration script starting..."
    log_info "Working directory: $(pwd)"
    log_info "Python path: ${PYTHONPATH:-not set}"
    
    # Check environment
    check_env_vars
    
    # Wait for database
    wait_for_db
    
    # Run migrations
    if run_migrations; then
        log_info "✅ All migrations completed successfully"
        exit 0
    else
        log_error "❌ Migration process failed"
        exit 1
    fi
}

# Run main function
main "$@"