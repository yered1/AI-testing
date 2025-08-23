#!/usr/bin/env bash
set -euo pipefail
if [ -z "${APK:-}" ]; then
  echo "Usage: APK=/path/to/app.apk API=http://localhost:8080 TENANT=t_demo bash $0"; exit 1
fi
API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
HDR=(-H "Content-Type: application/json" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")

echo "== Create engagement"
ENG=$(curl -s -X POST "$API/v1/engagements" "${HDR[@]}" -d '{"name":"mobile-apk","tenant_id":"'"$TENANT"'","type":"mobile","scope":{}}' | jq -r .id)

echo "== Auto-plan (default_mobile_static)"
AUTO=$(curl -s -X POST "$API/v2/engagements/$ENG/plan/auto" "${HDR[@]}" -d '{"preferences":{"packs":["default_mobile_static"]}}')
SEL=$(echo "$AUTO" | jq -c '{selected_tests: .selected_tests, agents: {}, risk_tier: "safe_passive"}')

echo "== Create plan & run"
PLAN=$(curl -s -X POST "$API/v1/engagements/$ENG/plan" "${HDR[@]}" -d "$SEL" | jq -r .id)
RUN=$(curl -s -X POST "$API/v1/tests" "${HDR[@]}" -d '{"engagement_id":"'"$ENG"'","plan_id":"'"$PLAN"'"}' | jq -r .id)
echo "RUN=$RUN"

echo "== Upload APK artifact"
curl -s -X POST "$API/v2/runs/$RUN/artifacts" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}" \
  -F "file=@${APK}" -F "label=mobile_apk" -F "kind=apk" | jq .

echo "== Issue agent token and start mobile agent"
TOKEN=$(curl -s -X POST "$API/v2/agent_tokens" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","name":"mobile_apk"}' | jq -r .token)
AGENT_TOKEN=$TOKEN docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.mobile_apk.yml up --build -d agent_mobile_apk

echo "Tail agent logs (30s)"
docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.mobile_apk.yml logs -f agent_mobile_apk & sleep 30; kill $! || true

echo "== List artifacts index"
curl -s "$API/v2/runs/$RUN/artifacts/index.json" "${HDR[@]}" | jq . | head -n 50
