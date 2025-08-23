#!/usr/bin/env bash
set -euo pipefail
: "${AGENT_TOKEN:?Set AGENT_TOKEN}"
: "${SSH_HOST:?Set SSH_HOST to your remote Kali IP/DNS}"
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.kali.remote.yml up --build -d agent_kali_remote
