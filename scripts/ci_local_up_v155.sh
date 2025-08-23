#!/usr/bin/env bash
set -euo pipefail

echo "== Build orchestrator image =="
docker compose -f infra/docker-compose.v2.yml build orchestrator

bash scripts/ci_migrate_v155.sh
bash scripts/ci_stack_up_v155.sh

echo "== Run smoke =="
python scripts/ci_smoke.py || { bash scripts/print_logs_on_fail_v155.sh; exit 1; }
