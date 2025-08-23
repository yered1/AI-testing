#!/usr/bin/env bash
set -euo pipefail
WF=".github/workflows/ci.yml"
if [ ! -f "$WF" ]; then
  echo "No existing ci.yml found; nothing to patch."
  exit 0
fi

# Ensure our compat override is used by augmenting 'compose up' lines
tmp=$(mktemp)
awk '
/docker compose .*docker-compose\.v2\.yml .* up -d/ {
  sub("up -d", "up -d -f infra/docker-compose.opa.compat.yml -f infra/docker-compose.health.yml");
}
{ print }
' "$WF" > "$tmp" && mv "$tmp" "$WF"

# Insert a migration step before API start if not present
if ! grep -q "Run DB migrations (one-off container)" "$WF"; then
  perl -0777 -pe "s/(- name: Start stack[\\s\\S]*?run:\\s*\\|[\\s\\S]*?up -d[\\s\\S]*?\\n)/- name: Build orchestrator image (for migration run)\\n  run: |\\n    docker compose -f infra\\/docker-compose.v2.yml build orchestrator\\n\\n- name: Start DB and OPA (compat image)\\n  run: |\\n    docker compose -f infra\\/docker-compose.v2.yml -f infra\\/docker-compose.opa.compat.yml up -d db opa\\n    echo \"Waiting for DB to be healthy...\"\\n    for i in \\$(seq 1 60); do\\n      if docker compose -f infra\\/docker-compose.v2.yml exec -T db pg_isready -U postgres >\\/dev\\/null 2>&1; then echo \"DB is healthy\"; break; fi\\n      sleep 2\\n    done\\n\\n- name: Run DB migrations (one-off container)\\n  run: |\\n    docker compose -f infra\\/docker-compose.v2.yml run --rm orchestrator alembic upgrade head\\n\\n- name: Start stack (API + DB + OPA) with CI overrides\\n  run: |\\n    docker compose -f infra\\/docker-compose.v2.yml -f infra\\/docker-compose.evidence.yml -f infra\\/docker-compose.ci.yml -f infra\\/docker-compose.opa.compat.yml -f infra\\/docker-compose.health.yml up -d\\n    echo \"Waiting for API to be ready...\"\\n    bash scripts\\/wait_for_api_v152.sh http:\\/\\/localhost:8080\\/health 180\\n/g" -i "$WF"
fi

echo "ci.yml patched."
