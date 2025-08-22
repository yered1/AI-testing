.PHONY: up down logs migrate ui-up ui-down smoke reset-db openapi

up:
	docker compose -f infra/docker-compose.v2.yml up --build -d

down:
	docker compose -f infra/docker-compose.v2.yml down

logs:
	docker compose -f infra/docker-compose.v2.yml logs -f orchestrator

migrate:
	docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

ui-up:
	docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.ui.yml up --build -d ui

ui-down:
	docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.ui.yml down

smoke:
	bash scripts/smoke.sh

reset-db:
	bash scripts/reset_db.sh

openapi:
	curl -s http://localhost:8080/openapi.json -o openapi.json
