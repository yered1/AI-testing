#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
HDR=(-H "Content-Type: application/json" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")

echo "== Create engagement (web)"
ENG=$(curl -s -X POST "$API/v1/engagements" "${HDR[@]}" -d '{"name":"artifacts","tenant_id":"'"$TENANT"'","type":"web","scope":{"in_scope_domains":["example.com"]}}' | jq -r .id)

echo "== Auto-plan with active pack"
AUTO=$(curl -s -X POST "$API/v2/engagements/$ENG/plan/auto" "${HDR[@]}" -d '{"preferences":{"packs":["default_web_active"]}}')
SEL=$(echo "$AUTO" | jq -c '{selected_tests: .selected_tests, agents: {}, risk_tier: "safe_active"}')

echo "== Validate + plan + run"
curl -s -X POST "$API/v2/engagements/$ENG/plan/validate" "${HDR[@]}" -d "$SEL" | jq .
PLAN=$(curl -s -X POST "$API/v1/engagements/$ENG/plan" "${HDR[@]}" -d "$SEL" | jq -r .id)
RUN=$(curl -s -X POST "$API/v1/tests" "${HDR[@]}" -d '{"engagement_id":"'"$ENG"'","plan_id":"'"$PLAN"'"}' | jq -r .id)
echo "RUN=$RUN"

echo "== Create agent token"
TOKEN=$(curl -s -X POST "$API/v2/agent_tokens" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","name":"zapv2"}' | jq -r .token)

echo "== Start zap v2 agent (baseline)"
AGENT_TOKEN=$TOKEN docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.zap.v2.yml up --build -d agent_zap_v2

echo "== Tail SSE briefly (30s)"
curl -s "$API/v2/runs/$RUN/events" "${HDR[@]}" --no-buffer | timeout 30 sed -n '1,80p' || true

echo "== List artifacts for run"
curl -s "$API/v2/runs/$RUN/artifacts" "${HDR[@]}" | jq . | head -n 60

echo "Done."
