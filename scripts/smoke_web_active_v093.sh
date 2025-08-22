#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
HDR=(-H "Content-Type: application/json" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")

echo "== Create engagement"
ENG=$(curl -s -X POST "$API/v1/engagements" "${HDR[@]}" -d '{"name":"web-active","tenant_id":"'"$TENANT"'","type":"web","scope":{"in_scope_domains":["example.com"]}}' | jq -r .id)

echo "== Auto-plan (with pack default_web_active)"
AUTO=$(curl -s -X POST "$API/v2/engagements/$ENG/plan/auto" "${HDR[@]}" -d '{"preferences":{"packs":["default_web_active"]}}')
SEL=$(echo "$AUTO" | jq -c '{selected_tests: .selected_tests, agents: {}, risk_tier: "safe_active"}')

echo "== Validate"
curl -s -X POST "$API/v2/engagements/$ENG/plan/validate" "${HDR[@]}" -d "$SEL" | jq .

echo "== Create plan & run"
PLAN=$(curl -s -X POST "$API/v1/engagements/$ENG/plan" "${HDR[@]}" -d "$SEL" | jq -r .id)
RUN=$(curl -s -X POST "$API/v1/tests" "${HDR[@]}" -d '{"engagement_id":"'"$ENG"'","plan_id":"'"$PLAN"'"}' | jq -r .id)
echo "RUN=$RUN"

echo "== Issue agent token"
TOKEN=$(curl -s -X POST "$API/v2/agent_tokens" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","name":"webagents"}' | jq -r .token)

echo "== Start ZAP and Nuclei agents"
AGENT_TOKEN="$TOKEN" bash scripts/agent_zap_up.sh
AGENT_TOKEN="$TOKEN" bash scripts/agent_nuclei_up.sh

echo "== Tail orchestrator events for a bit (30s)"
curl -s "$API/v2/runs/$RUN/events" "${HDR[@]}" --no-buffer | timeout 30 sed -n '1,40p' || true

echo "Done (agents keep running; stop with docker compose stop agent_zap agent_nuclei)."
