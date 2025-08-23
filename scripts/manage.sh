#!/bin/bash
# Unified management script for AI-Testing platform

set -e

COMMAND=${1:-help}
shift || true

case "$COMMAND" in
    up)
        docker compose -f infra/docker-compose.yml up -d "$@"
        ;;
    down)
        docker compose -f infra/docker-compose.yml down "$@"
        ;;
    logs)
        docker compose -f infra/docker-compose.yml logs -f "$@"
        ;;
    migrate)
        docker compose -f infra/docker-compose.yml exec orchestrator alembic upgrade head
        ;;
    test)
        python scripts/smoke_test.py "$@"
        ;;
    clean)
        bash scripts/cleanup.sh "$@"
        ;;
    agent)
        AGENT_TYPE=${1:-help}
        shift || true
        case "$AGENT_TYPE" in
            create-token)
                curl -s -X POST http://localhost:8080/v2/agent_tokens \
                    -H 'Content-Type: application/json' \
                    -d '{"name":"'${1:-agent}'"}' | jq -r .token
                ;;
            *)
                echo "Usage: $0 agent create-token [name]"
                ;;
        esac
        ;;
    help)
        echo "Usage: $0 [command] [options]"
        echo "Commands:"
        echo "  up       - Start services"
        echo "  down     - Stop services"
        echo "  logs     - View logs"
        echo "  migrate  - Run database migrations"
        echo "  test     - Run smoke tests"
        echo "  clean    - Clean up temporary files"
        echo "  agent    - Agent management"
        ;;
    *)
        echo "Unknown command: $COMMAND"
        exit 1
        ;;
esac
