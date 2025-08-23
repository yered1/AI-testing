#!/usr/bin/env bash
set -Eeuo pipefail
yml=".github/workflows/ci.yml"
if [ ! -f "$yml" ]; then
  echo "No existing $yml, skipping patch"; exit 0
fi
# Append steps after checkout to call our scripts; idempotent-ish.
if ! grep -q "ci_migrate_v156.sh" "$yml"; then
  cat >> "$yml" <<'EOF'

      - name: Migrate (DB+OPA up; alembic from /app/orchestrator)
        run: bash scripts/ci_migrate_v156.sh

      - name: Bring up full stack
        run: bash scripts/ci_stack_up_v156.sh

      - name: Wait for API
        run: bash scripts/wait_for_api_v156.sh

      - name: Smoke
        run: python scripts/ci_smoke.py

      - name: Print logs on fail
        if: failure()
        run: bash scripts/print_logs_on_fail_v156.sh
EOF
  echo "Patched $yml"
else
  echo "Patch already present in $yml"
fi
