#!/usr/bin/env bash
set -euo pipefail
URL="${1:-http://localhost:8080/health}"
TIMEOUT="${2:-120}"
echo "Waiting for $URL (timeout ${TIMEOUT}s)..."
end=$((SECONDS+TIMEOUT))
while [ $SECONDS -lt $end ]; do
  if curl -fsS "$URL" >/dev/null; then
    echo "API is up"
    exit 0
  fi
  sleep 2
done
echo "Timed out waiting for API at $URL"
exit 1
