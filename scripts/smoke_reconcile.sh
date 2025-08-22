#!/usr/bin/env bash
set -euo pipefail

API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
HDR=(-H "Content-Type: application/json" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")

echo "== Create engagement"
ENG=$(curl -s -X POST "$API/v1/engagements" "${HDR[@]}" -d '{"name":"demo","tenant_id":"'"$TENANT"'","type":"web","scope":{"in_scope_domains":["example.com"]}}' | jq -r .id)

echo "== Auto-plan"
AUTO=$(curl -s -X POST "$API/v2/engagements/$ENG/plan/auto" "${HDR[@]}")
echo "$AUTO" | jq .

SEL=$(echo "$AUTO" | jq -c '{selected_tests: .selected_tests, agents: {}, risk_tier: "safe_active"}')

echo "== Validate"
curl -s -X POST "$API/v2/engagements/$ENG/plan/validate" "${HDR[@]}" -d "$SEL" | jq .

echo "== Create plan"
PLAN=$(curl -s -X POST "$API/v1/engagements/$ENG/plan" "${HDR[@]}" -d "$SEL" | jq -r .id)

echo "== Start run"
RUN=$(curl -s -X POST "$API/v1/tests" "${HDR[@]}" -d '{"engagement_id":"'"$ENG"'","plan_id":"'"$PLAN"'"}' | jq -r .id)
echo "RUN=$RUN"

echo "== Post a finding"
curl -s -X POST "$API/v2/runs/$RUN/findings" "${HDR[@]}" -d '[{"title":"Example","severity":"low","description":"demo","assets":{"host":"example.com"}}]' | jq .

echo "== Download report (json)"
curl -s "$API/v2/reports/run/$RUN.json" "${HDR[@]}" | jq . | head -n 30

echo "Done. Attach SSE in the UI to see live events."
