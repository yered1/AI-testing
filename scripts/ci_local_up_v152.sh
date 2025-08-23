#!/usr/bin/env bash
set -euo pipefail
# Build image for migration
docker compose -f infra/docker-compose.v2.yml build orchestrator
# Start DB + OPA
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.opa.compat.yml up -d db opa
echo "Waiting for DB to be healthy..."
for i in $(seq 1 60); do
  if docker compose -f infra/docker-compose.v2.yml exec -T db pg_isready -U postgres >/dev/null 2>&1; then
    echo "DB is healthy"; break
  fi
  sleep 2
done
# Migrate
docker compose -f infra/docker-compose.v2.yml run --rm orchestrator alembic upgrade head
# Start API stack
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.evidence.yml -f infra/docker-compose.ci.yml -f infra/docker-compose.opa.compat.yml -f infra/docker-compose.health.yml up -d
# Wait for health
bash scripts/wait_for_api_v152.sh http://localhost:8080/health 180
echo "CI local stack is healthy."
