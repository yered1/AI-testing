#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
CIDR="${CIDR:-10.0.0.0/24}"
HDR=(-H "Content-Type: application/json" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")

ENG=$(curl -s -X POST "$API/v1/engagements" "${HDR[@]}" -d '{"name":"internal-net","tenant_id":"'"$TENANT"'","type":"network","scope":{"in_scope_cidrs":["'"$CIDR"'"]}}' | jq -r .id)
SEL='{"selected_tests":["network_discovery_ping_sweep","network_nmap_tcp_full","network_nmap_udp_top_200"],"agents":{},"risk_tier":"intrusive","params":{"network_discovery_ping_sweep":{"cidrs":["'"$CIDR"'"]},"network_nmap_tcp_full":{"cidrs":["'"$CIDR"'"]},"network_nmap_udp_top_200":{"cidrs":["'"$CIDR"'"]}}}'
curl -s -X POST "$API/v2/engagements/$ENG/plan/validate" "${HDR[@]}" -d "$SEL" | jq .
PLAN=$(curl -s -X POST "$API/v1/engagements/$ENG/plan" "${HDR[@]}" -d "$SEL" | jq -r .id)
RUN=$(curl -s -X POST "$API/v1/tests" "${HDR[@]}" -d '{"engagement_id":"'"$ENG"'","plan_id":"'"$PLAN"'"}' | jq -r .id)
echo "RUN=$RUN"
TOKEN=$(curl -s -X POST "$API/v2/agent_tokens" "${HDR[@]}" -d '{"tenant_id":"'"$TENANT"'","name":"net1"}' | jq -r .token)
AGENT_TOKEN="$TOKEN" ALLOW_ACTIVE_SCAN=1 bash scripts/agent_network_up.sh
curl -s "$API/v2/runs/$RUN/events" "${HDR[@]}" --no-buffer | timeout 30 sed -n '1,40p' || true
