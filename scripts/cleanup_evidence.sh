#!/usr/bin/env bash
set -euo pipefail
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.evidence.yml exec orchestrator bash -lc 'rm -rf /data/evidence/* || true'
echo "Evidence purged."
