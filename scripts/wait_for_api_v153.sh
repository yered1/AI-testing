#!/usr/bin/env bash
set -euo pipefail
URL="${1:-http://localhost:8080/health}"
TIMEOUT="${2:-60}"
echo "Waiting for API at $URL (timeout ${TIMEOUT}s)..."
end=$((SECONDS+TIMEOUT))
while [ $SECONDS -lt $end ]; do
  if curl -fsS "$URL" >/dev/null; then
    echo "API is up"; exit 0
  fi
  sleep 2
done
echo "ERROR: API did not become healthy within ${TIMEOUT}s"
exit 1
