#!/bin/bash
# Stop all orchestrator services

echo "🛑 Stopping AI Testing Orchestrator services..."

docker stop orchestrator-postgres orchestrator-redis orchestrator-opa 2>/dev/null || true
docker rm orchestrator-postgres orchestrator-redis orchestrator-opa 2>/dev/null || true
docker network rm orchestrator_network 2>/dev/null || true

echo "✅ All services stopped"
