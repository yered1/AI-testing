#!/usr/bin/env bash
set -euo pipefail
echo "== Orchestrator logs =="
docker compose -f infra/docker-compose.v2.yml logs --tail=200 orchestrator || true
echo "== DB logs =="
docker compose -f infra/docker-compose.v2.yml logs --tail=200 db || true
echo "== OPA logs =="
docker compose -f infra/docker-compose.v2.yml logs --tail=200 opa || true
