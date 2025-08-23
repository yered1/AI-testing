#!/bin/bash
# Production deployment script for AI-Testing platform

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}

echo "Deploying AI-Testing Platform"
echo "Environment: $ENVIRONMENT"
echo "Version: $VERSION"

# Validate environment
case "$ENVIRONMENT" in
    staging|production)
        ;;
    *)
        echo "Invalid environment. Use: staging or production"
        exit 1
        ;;
esac

# Load environment configuration
if [ -f "config/$ENVIRONMENT.env" ]; then
    source "config/$ENVIRONMENT.env"
else
    echo "Configuration file not found: config/$ENVIRONMENT.env"
    exit 1
fi

# Pre-deployment checks
echo "Running pre-deployment checks..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed"
    exit 1
fi

# Check required environment variables
required_vars=(
    "DATABASE_URL"
    "REDIS_URL"
    "SECRET_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Required environment variable not set: $var"
        exit 1
    fi
done

# Build images
echo "Building Docker images..."
docker-compose -f infra/docker-compose.yml build

# Run database migrations
echo "Running database migrations..."
docker-compose -f infra/docker-compose.yml run --rm orchestrator alembic upgrade head

# Deploy services
echo "Deploying services..."
docker-compose -f infra/docker-compose.yml up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Health checks
services=("orchestrator" "db" "redis")
for service in "${services[@]}"; do
    if docker-compose -f infra/docker-compose.yml ps | grep -q "$service.*Up"; then
        echo "✓ $service is running"
    else
        echo "✗ $service failed to start"
        exit 1
    fi
done

# Run smoke tests
echo "Running smoke tests..."
python scripts/smoke_test.py

echo "Deployment completed successfully!"
echo "Access the application at: https://$DOMAIN"
