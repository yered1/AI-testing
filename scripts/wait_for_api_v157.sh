#!/usr/bin/env bash
set -euo pipefail
API_URL="${API_URL:-http://localhost:8080/health}"
echo "Waiting for API to be ready..."
for i in $(seq 1 90); do
  if curl -fsS "$API_URL" >/dev/null; then echo "API is up"; exit 0; fi
  sleep 2
done
echo "API did not become healthy in time"; exit 1
