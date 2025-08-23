#!/usr/bin/env bash
set -euo pipefail
WF=".github/workflows/ci.yml"
if [ ! -f "$WF" ]; then
  echo "No existing ci.yml found; skipping patch."; exit 0
fi
# Simple best-effort patch: insert calls to migration and wait scripts before smoke
tmp=$(mktemp)
awk '
/docker compose .*build/ { print; built=1; next }
{ print }
END {
  if (!built) print "      - name: Build orchestrator\n        run: docker compose -f infra/docker-compose.v2.yml build orchestrator"
  print "      - name: Migrate DB (CI)"
  print "        run: bash scripts/ci_migrate_v157.sh"
  print "      - name: Bring up stack"
  print "        run: bash scripts/ci_stack_up_v157.sh"
  print "      - name: Wait for API"
  print "        run: bash scripts/wait_for_api_v157.sh"
}' "$WF" > "$tmp"
mv "$tmp" "$WF"
echo "Patched $WF"
