#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
echo "== Waiting for API $API/health"
for i in $(seq 1 60); do
  if curl -fsS "$API/health" >/dev/null; then echo "API is up"; exit 0; fi
  sleep 2
done
echo "API did not become healthy in time"; exit 1
