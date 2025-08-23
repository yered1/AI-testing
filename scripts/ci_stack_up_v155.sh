#!/usr/bin/env bash
set -euo pipefail
BASE="-f infra/docker-compose.v2.yml"
OPA="-f infra/docker-compose.opa.compat.yml"
DB="-f infra/docker-compose.db.ci.yml"
EVI="-f infra/docker-compose.evidence.yml"
CI="-f infra/docker-compose.ci.yml"

echo "== Bring up full stack =="
docker compose $BASE $OPA $DB $EVI $CI up -d

bash scripts/wait_for_api_v155.sh
