#!/usr/bin/env bash
set -euo pipefail

COMPOSE_BASE="-f infra/docker-compose.v2.yml -f infra/docker-compose.opa.compat.yml -f infra/docker-compose.db.ci.yml -f infra/docker-compose.health.yml"

echo "== Bring up DB+OPA and wait for DB healthy"
docker compose $COMPOSE_BASE up -d db opa

echo "== Waiting for DB health..."
for i in $(seq 1 60); do
  if docker compose -f infra/docker-compose.v2.yml exec -T db pg_isready -U postgres -d aitest >/dev/null 2>&1; then
    echo "DB is healthy"
    break
  fi
  sleep 2
  if [ "$i" -eq 60 ]; then
    echo "DB did not become healthy"; exit 1
  fi
done

echo "== Running Alembic migrations (with PYTHONPATH and working dir)"
docker compose $COMPOSE_BASE run --rm --no-deps \
  -e PYTHONPATH=/app \
  -w /app \
  orchestrator \
  bash -lc 'alembic -c orchestrator/alembic.ini upgrade head'
