#!/usr/bin/env bash
set -euo pipefail
AGENT_TOKEN="${AGENT_TOKEN:-}"
if [ -z "$AGENT_TOKEN" ]; then
  echo "Set AGENT_TOKEN env (from POST /v2/agent_tokens)"; exit 1
fi
AGENT_TOKEN="$AGENT_TOKEN" docker compose   -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.semgrep.yml up --build -d agent_semgrep
