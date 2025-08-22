#!/usr/bin/env bash
set -euo pipefail
echo "This will REMOVE the Postgres volume 'db_data'. Ctrl-C to abort."
sleep 2
docker compose -f infra/docker-compose.v2.yml down -v
docker volume rm $(docker volume ls -q | grep db_data) || true
echo "Done. Bring stack back up and re-run migrations."
