#!/usr/bin/env bash
set -euo pipefail
cp -n infra/auth/.env.auth.example infra/auth/.env.auth || true
echo "Edit infra/auth/.env.auth with your IdP settings (issuer, client id/secret)."
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.auth-rbac.yml up -d reverse-proxy oauth2-proxy
echo "RBAC proxy listening at http://localhost:8081"
