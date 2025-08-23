#!/usr/bin/env bash
set -euo pipefail
YML=".github/workflows/ci.yml"
if [ ! -f "$YML" ]; then
  echo "No existing ci.yml found; use ci_v4.yml instead."; exit 0
fi
# Append compose overrides to every compose call and run alembic with env/path
tmp="$YML.tmp.$RANDOM"
sed -E 's#docker compose -f infra/docker-compose.v2.yml (up|run|exec|down)#docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.opa.compat.yml -f infra/docker-compose.db.ci.yml -f infra/docker-compose.health.yml \1#g' "$YML" > "$tmp"

# Ensure migrate step uses --no-deps, PYTHONPATH and working dir
sed -E -i 's#alembic upgrade head#bash -lc "PYTHONPATH=/app alembic -c orchestrator/alembic.ini upgrade head"#g' "$tmp"

mv "$tmp" "$YML"
echo "Patched $YML"
