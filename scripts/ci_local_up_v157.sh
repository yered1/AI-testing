#!/usr/bin/env bash
set -euo pipefail
# Build base images
docker compose -f infra/docker-compose.v2.yml build orchestrator
# Migrate
bash scripts/ci_migrate_v157.sh
# Bring up stack
bash scripts/ci_stack_up_v157.sh
# Wait for API
bash scripts/wait_for_api_v157.sh
