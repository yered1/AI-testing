#!/usr/bin/env bash
set -euo pipefail
COMPOSE="-f infra/docker-compose.v2.yml"
echo "== Orchestrator logs =="
docker compose $COMPOSE logs --tail=200 orchestrator || true
echo "== DB logs =="
docker compose $COMPOSE logs --tail=200 db || true
echo "== OPA logs =="
docker compose $COMPOSE logs --tail=200 opa || true
