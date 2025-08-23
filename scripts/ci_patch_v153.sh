#!/usr/bin/env bash
set -euo pipefail

wf=".github/workflows/ci.yml"
if [ ! -f "$wf" ]; then
  echo "No existing ci.yml found. You can use .github/workflows/ci_v3.yml instead."
  exit 0
fi

# Add compose overrides to all docker compose commands
tmp="$(mktemp)"
awk '
  {
    line=$0
    if (line ~ /docker compose .*infra\/docker-compose.v2.yml/ && line !~ /opa.compat/) {
      sub(/infra\/docker-compose.v2.yml/, "infra/docker-compose.v2.yml -f infra/docker-compose.opa.compat.yml -f infra/docker-compose.db.ci.yml", line)
    }
    # add --no-deps to any compose run orchestrator
    if (line ~ /docker compose .* run .* orchestrator / && line !~ /--no-deps/) {
      gsub(/ run /, " run --no-deps ", line)
    }
    print line
  }
' "$wf" > "$tmp"
mv "$tmp" "$wf"

# Insert DB health wait if not present
if ! grep -q "Waiting for DB health" "$wf"; then
  cat >> "$wf" <<'EOF'

      - name: Wait for DB health
        run: |
          echo "Waiting for DB health..."
          for i in $(seq 1 60); do
            status=$(docker inspect --format='{{.State.Health.Status}}' $(docker compose -f infra/docker-compose.v2.yml ps -q db) 2>/dev/null || echo "starting")
            if [ "$status" = "healthy" ]; then echo "DB is healthy"; break; fi
            sleep 2
          done
EOF
fi

# Add wait_for_api script usage if missing
if ! grep -q "wait_for_api_v153.sh" "$wf"; then
  cat >> "$wf" <<'EOF'

      - name: Wait for API
        run: |
          bash scripts/wait_for_api_v153.sh http://localhost:8080/health 90
EOF
fi

echo "ci.yml patched."
