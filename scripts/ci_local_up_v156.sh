#!/usr/bin/env bash
set -Eeuo pipefail
bash scripts/ci_migrate_v156.sh
bash scripts/ci_stack_up_v156.sh
bash scripts/wait_for_api_v156.sh || { bash scripts/print_logs_on_fail_v156.sh; exit 1; }
python scripts/ci_smoke.py
