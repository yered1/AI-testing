#!/usr/bin/env bash
set -euo pipefail
WF=".github/workflows/ci.yml"
if [ ! -f "$WF" ]; then
  echo "No $WF found. Are you at repo root?" >&2
  exit 1
fi

# Add the extra compose file to the 'up -d --build' line and to 'logs' lines (idempotent)
tmp="$(mktemp)"
awk '
  /docker compose/ && /-f infra\/docker-compose.v2.yml/ && /up -d --build/ {
    if ($0 ~ /docker-compose.opa.compat.yml/) { print; next }
    sub(/up -d --build/, "-f infra/docker-compose.opa.compat.yml up -d --build")
    print; next
  }
  /docker compose/ && /logs/ && /orchestrator/ {
    if ($0 ~ /docker-compose.opa.compat.yml/) { print; next }
    sub(/-f infra\/docker-compose.v2.yml/, "& -f infra/docker-compose.opa.compat.yml")
    print; next
  }
  /docker compose/ && /logs/ && /opa/ {
    if ($0 ~ /docker-compose.opa.compat.yml/) { print; next }
    sub(/-f infra\/docker-compose.v2.yml/, "& -f infra/docker-compose.opa.compat.yml")
    print; next
  }
  { print }
' "$WF" > "$tmp"
if cmp -s "$WF" "$tmp"; then
  echo "ci.yml already patched (no changes)."
  rm -f "$tmp"
else
  mv "$tmp" "$WF"
  echo "Patched $WF to include infra/docker-compose.opa.compat.yml"
fi
