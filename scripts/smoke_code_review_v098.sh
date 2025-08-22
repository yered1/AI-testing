#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
HDR=(-H "Content-Type: application/json" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")

echo "== Create code engagement"
ENG=$(curl -s -X POST "$API/v1/engagements" "${HDR[@]}" -d '{"name":"code-review","tenant_id":"'"$TENANT"'","type":"code","scope":{}}' | jq -r .id)

echo "== Auto-plan with default_code_review"
AUTO=$(curl -s -X POST "$API/v2/engagements/$ENG/plan/auto" "${HDR[@]}" -d '{"preferences":{"packs":["default_code_review"]}}')
SEL=$(echo "$AUTO" | jq -c '{selected_tests: .selected_tests, agents: {}, risk_tier: "safe_passive"}')

echo "== Create plan & run"
PLAN=$(curl -s -X POST "$API/v1/engagements/$ENG/plan" "${HDR[@]}" -d "$SEL" | jq -r .id)
RUN=$(curl -s -X POST "$API/v1/tests" "${HDR[@]}" -d '{"engagement_id":"'"$ENG"'","plan_id":"'"$PLAN"'"}' | jq -r .id)
echo "RUN=$RUN"

echo "== Create sample code and upload as artifact"
mkdir -p /tmp/code_smoke && cat >/tmp/code_smoke/app.py <<'PY'
def insecure(cmd):
    import os
    os.system(cmd)  # BAD: command injection risk
PY
(cd /tmp && tar -czf code_smoke.tgz code_smoke)
curl -s -X POST "$API/v2/runs/$RUN/artifacts" -H "X-Tenant-Id: ${TENANT}" -F "file=@/tmp/code_smoke.tgz" -F "label=code_package" -F "kind=code" | jq .

echo "== Issue agent token"
TOKEN=$(curl -s -X POST "$API/v2/agent_tokens" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","name":"semgrep1"}' | jq -r .token)

echo "== Start semgrep agent"
AGENT_TOKEN=$TOKEN docker compose -f infra/docker-compose.v2.yml -f infra/docker-compose.agents.semgrep.yml up --build -d agent_semgrep

echo "== Wait and fetch findings"
sleep 20
curl -s "$API/v2/runs/$RUN/findings" -H "X-Tenant-Id: ${TENANT}" | jq . | head -n 60
