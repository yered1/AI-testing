#!/usr/bin/env bash
set -euo pipefail
cp -n infra/auth/.env.auth.example infra/auth/.env.auth || true
echo "Edit infra/auth/.env.auth with your OIDC provider settings."
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.auth.yml up -d reverse-proxy oauth2-proxy
echo "Open http://localhost:8081 (OIDC-protected)"
