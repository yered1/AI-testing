#!/usr/bin/env bash
set -Eeuo pipefail
URL="${1:-http://localhost:8080/health}"
TRIES="${TRIES:-60}"
SLEEP="${SLEEP:-2}"

echo "Waiting for API (${URL}) to be ready..."
for i in $(seq 1 "${TRIES}"); do
  if curl -fsS "$URL" >/dev/null 2>&1; then echo "API is up"; exit 0; fi
  sleep "${SLEEP}"
done
echo "API did not become ready within $((TRIES*SLEEP))s"
exit 1
