#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
echo "Waiting for API ($API/health) ..."
for i in $(seq 1 90); do
  if curl -fsS "$API/health" >/dev/null 2>&1; then
    echo "API is up"; exit 0
  fi
  sleep 2
done
echo "API did not become healthy"
exit 1
