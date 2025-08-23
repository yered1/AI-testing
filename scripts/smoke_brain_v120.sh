#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
HDR=(-H "Content-Type: application/json" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")

echo "== Create engagement (web external)"
ENG=$(curl -s -X POST "$API/v1/engagements" "${HDR[@]}" -d '{"name":"brain-v3","tenant_id":"'"$TENANT"'","type":"external","scope":{"in_scope_domains":["example.com"]}}' | jq -r .id)

echo "== Brain v3 plan (heuristic)"
PLAN3=$(curl -s -X POST "$API/v3/brain/plan" "${HDR[@]}" -d '{"engagement_id":"'"$ENG"'","preferences":{"risk_tier":"safe_active"}}')
echo "$PLAN3" | jq . | head -n 30

SEL=$(echo "$PLAN3" | jq -c '{selected_tests: .selected_tests, agents: {}, risk_tier: "safe_active"}')

echo "== Enrich"
ENR=$(curl -s -X POST "$API/v3/brain/enrich" "${HDR[@]}" -d '{"engagement_id":"'"$ENG"'","selected_tests": '"$SEL"'}')
echo "$ENR" | jq . | head -n 30

echo "== Validate + plan + run"
VAL=$(curl -s -X POST "$API/v2/engagements/$ENG/plan/validate" "${HDR[@]}" -d "$SEL" | jq .)
PLAN=$(curl -s -X POST "$API/v1/engagements/$ENG/plan" "${HDR[@]}" -d "$SEL" | jq -r .id)
RUN=$(curl -s -X POST "$API/v1/tests" "${HDR[@]}" -d '{"engagement_id":"'"$ENG"'","plan_id":"'"$PLAN"'"}' | jq -r .id)
echo "RUN=$RUN"

echo "== Token + discovery agent"
TOKEN=$(curl -s -X POST "$API/v2/agent_tokens" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","name":"discovery"}' | jq -r .token)
AGENT_TOKEN="$TOKEN" bash scripts/agent_web_discovery_up.sh

echo "== Tail events (30s)"
curl -s "$API/v2/runs/$RUN/events" "${HDR[@]}" --no-buffer | timeout 30 sed -n '1,80p' || true
