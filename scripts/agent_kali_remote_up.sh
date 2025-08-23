#!/usr/bin/env bash
set -euo pipefail
: "${AGENT_TOKEN:?Set AGENT_TOKEN from POST /v2/agent_tokens}"
if [ -z "${SSH_HOST:-}" ]; then echo "SSH_HOST is required (remote Kali host)"; exit 1; fi
if [ -z "${SSH_USER:-}" ]; then echo "SSH_USER is required"; exit 1; fi
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.kali.remote.yml up --build -d agent_kali_remote
echo "Kali remote agent started."
