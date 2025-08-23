#!/usr/bin/env bash
set -euo pipefail
echo "---- logs: orchestrator ----"
docker compose -f infra/docker-compose.v2.yml logs --tail=200 orchestrator || true
echo "---- logs: db ----"
docker compose -f infra/docker-compose.v2.yml logs --tail=200 db || true
echo "---- logs: opa ----"
docker compose -f infra/docker-compose.v2.yml logs --tail=200 opa || true
