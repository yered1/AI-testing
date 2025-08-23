#!/usr/bin/env bash
set -euo pipefail

BASE="-f infra/docker-compose.v2.yml"
OPA="-f infra/docker-compose.opa.compat.yml"
DB="-f infra/docker-compose.db.ci.yml"
HL="-f infra/docker-compose.health.yml"

echo "== Bring up DB + OPA (compat) =="
docker compose $BASE $OPA $DB $HL up -d db opa

echo "== Wait for DB to be ready =="
for i in $(seq 1 60); do
  if docker compose -f infra/docker-compose.v2.yml exec -T db pg_isready -U ${POSTGRES_USER:-postgres} >/dev/null 2>&1; then
    echo "DB is ready"; break
  fi
  sleep 2
  if [ "$i" -eq 60 ]; then
    echo "DB not ready after 120s"; exit 1
  fi
done

echo "== Run Alembic migrations (workdir=/app/orchestrator, PYTHONPATH=/app) =="
docker compose $BASE $OPA $DB $HL run --rm --no-deps \
  -e PYTHONPATH=/app -w /app/orchestrator orchestrator \
  bash -lc 'alembic -c alembic.ini upgrade head'
