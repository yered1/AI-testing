#!/usr/bin/env bash
set -euo pipefail
# Compose files
CF=(-f infra/docker-compose.v2.yml -f infra/docker-compose.opa.compat.yml -f infra/docker-compose.db.ci.yml -f infra/docker-compose.health.yml)

echo "== Bring up DB+OPA (detached) =="
docker compose "${CF[@]}" up -d db opa

echo "== Wait for DB to be healthy =="
for i in $(seq 1 60); do
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$(docker compose "${CF[@]}" ps -q db)" || echo "unknown")
  if [ "$STATUS" = "healthy" ]; then echo "DB is healthy"; break; fi
  sleep 2
done

echo "== Run Alembic migrations (workdir=/app/orchestrator, PYTHONPATH=/app) =="
docker compose "${CF[@]}" run --rm --no-deps \
  -e PYTHONPATH=/app -w /app/orchestrator orchestrator \
  bash -lc 'python -m pip install --no-cache-dir psycopg2-binary==2.9.9 >/dev/null 2>&1 || true; alembic -c alembic.ci.ini upgrade head'
