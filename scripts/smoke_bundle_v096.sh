#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
HDR=(-H "Content-Type: application/json" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")

echo "== Create engagement"
ENG=$(curl -s -X POST "$API/v1/engagements" "${HDR[@]}" -d '{"name":"bundle","tenant_id":"'"$TENANT"'","type":"web","scope":{"in_scope_domains":["example.com"]}}' | jq -r .id)

echo "== Auto-plan (default_web_active)"
AUTO=$(curl -s -X POST "$API/v2/engagements/$ENG/plan/auto" "${HDR[@]}" -d '{"preferences":{"packs":["default_web_active"]}}')
SEL=$(echo "$AUTO" | jq -c '{selected_tests: .selected_tests, agents: {}, risk_tier: "safe_active"}')

echo "== Plan & run"
PLAN=$(curl -s -X POST "$API/v1/engagements/$ENG/plan" "${HDR[@]}" -d "$SEL" | jq -r .id)
RUN=$(curl -s -X POST "$API/v1/tests" "${HDR[@]}" -d '{"engagement_id":"'"$ENG"'","plan_id":"'"$PLAN"'"}' | jq -r .id)
echo "RUN=$RUN"

echo "== Agent token"
TOKEN=$(curl -s -X POST "$API/v2/agent_tokens" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","name":"webagents"}' | jq -r .token)

echo "== Start v2 agents"
AGENT_TOKEN=$TOKEN bash scripts/agent_zap_v2_up.sh
AGENT_TOKEN=$TOKEN bash scripts/agent_nuclei_v2_up.sh

echo "== Wait 20s for artifacts"
sleep 20

echo "== Download bundle zip"
curl -s -L "$API/v2/reports/run/$RUN.zip" "${HDR[@]}" -o "run_${RUN}_bundle.zip"
ls -lh "run_${RUN}_bundle.zip" || true
echo "Done."
