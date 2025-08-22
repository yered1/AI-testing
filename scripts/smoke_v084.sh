#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
HDR=(-H "Content-Type: application/json" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")

echo "== Catalog =="
curl -s "$API/v1/catalog" "${HDR[@]}" | jq . | head -n 20

echo "== Create engagement"
ENG=$(curl -s -X POST "$API/v1/engagements" "${HDR[@]}" -d '{"name":"v084","tenant_id":"'"$TENANT"'","type":"web","scope":{"in_scope_domains":["example.com"]}}' | jq -r .id)

echo "== Auto-plan"
AUTO=$(curl -s -X POST "$API/v2/engagements/$ENG/plan/auto" "${HDR[@]}")
SEL=$(echo "$AUTO" | jq -c '{selected_tests: .selected_tests, agents: {}, risk_tier: "safe_active"}')

echo "== Validate"
curl -s -X POST "$API/v2/engagements/$ENG/plan/validate" "${HDR[@]}" -d "$SEL" | jq .

echo "== Create plan & run"
PLAN=$(curl -s -X POST "$API/v1/engagements/$ENG/plan" "${HDR[@]}" -d "$SEL" | jq -r .id)
RUN=$(curl -s -X POST "$API/v1/tests" "${HDR[@]}" -d '{"engagement_id":"'"$ENG"'","plan_id":"'"$PLAN"'"}' | jq -r .id)
echo "RUN=$RUN"

echo "== Quotas"
curl -s -X POST "$API/v2/quotas" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","monthly_budget":200,"per_plan_cap":50}' | jq .
curl -s "$API/v2/quotas/$TENANT" "${HDR[@]}" | jq .

echo "== Approvals"
APP=$(curl -s -X POST "$API/v2/approvals" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","engagement_id":"'"$ENG"'","reason":"demo"}' | jq -r .id)
curl -s -X POST "$API/v2/approvals/$APP/decide" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","decision":"approved"}' | jq .
curl -s "$API/v2/approvals?engagement_id=$ENG" "${HDR[@]}" | jq .

echo "== Findings & Reports"
curl -s -X POST "$API/v2/runs/$RUN/findings" "${HDR[@]}" -d '[{"title":"Sample","severity":"low","description":"demo finding"}]' | jq .
curl -s "$API/v2/runs/$RUN/findings" "${HDR[@]}" | jq . | head -n 20
curl -s "$API/v2/reports/run/$RUN.json" "${HDR[@]}" | jq . | head -n 20
curl -s "$API/v2/reports/run/$RUN.md" "${HDR[@]}" | head -n 20

echo "== Agent token + start dev agent"
TOKEN=$(curl -s -X POST "$API/v2/agent_tokens" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","name":"dev1"}' | jq -r .token)
AGENT_TOKEN=$TOKEN docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.dev.yml up --build -d agent_dev1

echo "== Recent runs"
curl -s "$API/v2/runs/recent" "${HDR[@]}" | jq . | head -n 20

echo "Done."
