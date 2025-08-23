#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
HDR=(-H "Content-Type: application/json" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")

echo "== Plan (guarded)"
PLAN=$(curl -s -X POST "$API/v3/brain/plan/guarded" -H "Content-Type: application/json" -H "X-Tenant-Id: ${TENANT}"   -d '{"engagement_type":"web","scope":{"in_scope_domains":["example.com"]},"preferences":{"provider":"heuristic"}}')
echo "$PLAN" | jq .

echo "== Start discovery agent (if not already)"
TOKEN=$(curl -s -X POST "$API/v2/agent_tokens" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","name":"discover2"}' | jq -r .token)
AGENT_TOKEN="$TOKEN" bash scripts/agent_web_discovery_up.sh || true

echo "== Done (use Builder to finalize plan/run)"
