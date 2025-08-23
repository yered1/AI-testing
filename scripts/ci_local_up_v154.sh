#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci_migrate_v154.sh
bash scripts/ci_stack_up_v154.sh
bash scripts/wait_for_api_v154.sh
