#!/usr/bin/env bash
set -euo pipefail
FILE=".github/workflows/ci.yml"
if [ ! -f "$FILE" ]; then
  echo "No existing ci.yml found; consider adding .github/workflows/ci_v5.yml"; exit 0
fi
# This is a best-effort patch: add calls to our scripts and include overrides.
tmp="$(mktemp)"
awk '
/docker compose .* build orchestrator/ { built=1 }
/alembic upgrade head/ { skip=1 }
{ print }
END {
  if (built!=1) print "      - name: Build orchestrator image\n        run: |\n          docker compose -f infra/docker-compose.v2.yml build orchestrator"
  print "      - name: Migrate (alembic with PYTHONPATH)"
  print "        run: |"
  print "          bash scripts/ci_migrate_v155.sh"
  print "      - name: Bring up full stack"
  print "        run: |"
  print "          bash scripts/ci_stack_up_v155.sh"
  print "      - name: Wait for API & smoke"
  print "        run: |"
  print "          python scripts/ci_smoke.py"
}' "$FILE" > "$tmp"
mv "$tmp" "$FILE"
echo "Patched $FILE"
