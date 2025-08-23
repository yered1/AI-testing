#!/usr/bin/env bash
set -euo pipefail
set -x
docker compose -f infra/docker-compose.v2.yml build orchestrator
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.opa.compat.yml -f infra/docker-compose.db.ci.yml -f infra/docker-compose.health.yml up -d db opa
echo "Waiting for DB health..."
for i in $(seq 1 60); do
  status=$(docker inspect --format='{{.State.Health.Status}}' $(docker compose -f infra/docker-compose.v2.yml ps -q db) 2>/dev/null || echo "starting")
  if [ "$status" = "healthy" ]; then echo "DB is healthy"; break; fi
  sleep 2
done
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.opa.compat.yml -f infra/docker-compose.db.ci.yml run --rm --no-deps orchestrator alembic upgrade head
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.opa.compat.yml -f infra/docker-compose.db.ci.yml -f infra/docker-compose.ci.yml up -d
bash scripts/wait_for_api_v153.sh http://localhost:8080/health 90
