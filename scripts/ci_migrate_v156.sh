#!/usr/bin/env bash
set -Eeuo pipefail

# Compose files to use during CI migration
CF=(-f infra/docker-compose.v2.yml \
    -f infra/docker-compose.opa.compat.yml \
    -f infra/docker-compose.db.ci.yml \
    -f infra/docker-compose.health.yml \
    -f infra/docker-compose.ci.pylibs.yml)

echo "== Build orchestrator base =="
docker compose -f infra/docker-compose.v2.yml build orchestrator

echo "== Build orchestrator (CI pylibs: psycopg2-binary) =="
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.ci.pylibs.yml build orchestrator

echo "== Up DB + OPA only (with compat & health) =="
docker compose "${CF[@]}" up -d db opa

echo "== Wait for DB to be healthy =="
for i in $(seq 1 90); do
  if docker compose "${CF[@]}" exec -T db pg_isready -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-aitest}" -h 127.0.0.1 >/dev/null 2>&1; then
    echo "DB is healthy"; break
  fi
  sleep 2
  if [ "$i" -eq 90 ]; then
    echo "DB did not become healthy"; exit 1
  fi
done

echo "== Run Alembic migrations (workdir=/app/orchestrator, PYTHONPATH=/app) =="
docker compose "${CF[@]}" run --rm --no-deps -e PYTHONPATH=/app -w /app/orchestrator orchestrator \
  bash -lc 'alembic -c alembic.ini upgrade head'
