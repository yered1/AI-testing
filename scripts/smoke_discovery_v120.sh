#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
HDR=(-H "Content-Type: application/json" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")

ENG=$(curl -s -X POST "$API/v1/engagements" "${HDR[@]}" -d '{"name":"discover","tenant_id":"'"$TENANT"'","type":"external","scope":{"in_scope_domains":["example.com","example.org"]}}' | jq -r .id)
SEL='{"selected_tests":[{"id":"network_dnsx_resolve","params":{"domains":["example.com","example.org"]}},{"id":"web_httpx_probe","params":{"targets":["https://example.com"]}}],"agents":{},"risk_tier":"safe_active"}'
PLAN=$(curl -s -X POST "$API/v1/engagements/$ENG/plan" "${HDR[@]}" -d "$SEL" | jq -r .id)
RUN=$(curl -s -X POST "$API/v1/tests" "${HDR[@]}" -d '{"engagement_id":"'"$ENG"'","plan_id":"'"$PLAN"'"}' | jq -r .id)
echo "RUN=$RUN"
TOKEN=$(curl -s -X POST "$API/v2/agent_tokens" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","name":"discovery"}' | jq -r .token)
AGENT_TOKEN="$TOKEN" bash scripts/agent_web_discovery_up.sh
curl -s "$API/v2/runs/$RUN/events" "${HDR[@]}" --no-buffer | timeout 20 sed -n '1,80p' || true
