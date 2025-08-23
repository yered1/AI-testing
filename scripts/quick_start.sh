#!/bin/bash
# Quick start script for AI Testing Orchestrator

set -e

echo "🚀 Starting AI Testing Orchestrator..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Create network
docker network create orchestrator_network 2>/dev/null || true

# Start PostgreSQL
echo "Starting PostgreSQL..."
docker run -d \
    --name orchestrator-postgres \
    --network orchestrator_network \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=orchestrator \
    -p 5432:5432 \
    postgres:15 2>/dev/null || echo "PostgreSQL already running"

# Start Redis
echo "Starting Redis..."
docker run -d \
    --name orchestrator-redis \
    --network orchestrator_network \
    -p 6379:6379 \
    redis:7 2>/dev/null || echo "Redis already running"

# Start OPA
echo "Starting OPA..."
docker run -d \
    --name orchestrator-opa \
    --network orchestrator_network \
    -v $(pwd)/policies_enabled:/policies:ro \
    -p 8181:8181 \
    openpolicyagent/opa:0.65.0 \
    run --server --addr=0.0.0.0:8181 /policies 2>/dev/null || echo "OPA already running"

# Wait for services
echo "Waiting for services to start..."
sleep 5

# Run migrations
echo "Running database migrations..."
cd orchestrator
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/orchestrator
export PYTHONPATH=$(pwd):$PYTHONPATH

if command -v alembic &> /dev/null; then
    alembic upgrade head || echo "Migration failed - continuing anyway"
else
    echo "Alembic not installed - skipping migrations"
fi

cd ..

# Start orchestrator
echo "Starting orchestrator..."
cd orchestrator
uvicorn routers.app:app --host 0.0.0.0 --port 8080 --reload
