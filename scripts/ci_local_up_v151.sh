#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
echo "Bringing up stack with OPA compat override..."
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.evidence.yml -f infra/docker-compose.ci.yml -f infra/docker-compose.opa.compat.yml up -d --build
echo "Waiting for API to be ready at $API/health ..."
for i in $(seq 1 90); do
  if curl -fsS "$API/health" >/dev/null; then
    echo "API is up"
    exit 0
  fi
  sleep 2
done
echo "Timed out waiting for API"; exit 1
