#!/usr/bin/env bash
set -euo pipefail
CF=(-f infra/docker-compose.v2.yml -f infra/docker-compose.evidence.yml -f infra/docker-compose.ci.yml -f infra/docker-compose.opa.compat.yml -f infra/docker-compose.db.ci.yml -f infra/docker-compose.health.yml)
echo "== Bring up full stack =="
docker compose "${CF[@]}" up -d
