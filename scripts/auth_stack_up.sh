#!/usr/bin/env bash
set -euo pipefail
cp -n infra/auth/.env.auth.example infra/auth/.env.auth || true
echo "Edit infra/auth/.env.auth with your OIDC settings, then run:"
echo "docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.auth.yml up -d reverse-proxy oauth2-proxy"
