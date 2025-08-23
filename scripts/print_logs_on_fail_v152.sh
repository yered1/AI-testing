#!/usr/bin/env bash
set -euo pipefail
FILES=(orchestrator db opa)
for S in "${FILES[@]}"; do
  echo "---- logs: $S ----"
  docker compose -f infra/docker-compose.v2.yml logs --tail=200 "$S" || true
done
