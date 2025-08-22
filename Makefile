.PHONY: up down migrate logs ui-up ui-down smoke agent-devext clean

up:
	docker compose -f infra/docker-compose.v2.yml up --build -d

down:
	docker compose -f infra/docker-compose.v2.yml down -v

migrate:
	docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head

logs:
	docker compose -f infra/docker-compose.v2.yml logs -f orchestrator

ui-up:
	docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.ui.yml up --build -d ui

ui-down:
	docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.ui.yml stop ui

smoke:
	API=http://localhost:8080 TENANT=t_demo bash scripts/smoke_v084.sh

agent-devext:
	@echo "Ensure you created a token: POST /v2/agent_tokens"
	@echo "Then run: AGENT_TOKEN=<token> bash scripts/agent_devext_up.sh"

clean:
	docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.evidence.yml exec orchestrator bash -lc 'rm -rf /data/evidence/* || true'
