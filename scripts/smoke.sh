#!/usr/bin/env bash
set -euo pipefail

BASE=${BASE:-http://localhost:8080}
USER=${USER:-yered}
EMAIL=${EMAIL:-yered@example.com}
TENANT=${TENANT:-t_demo}

hdr=(-H "X-Dev-User: $USER" -H "X-Dev-Email: $EMAIL" -H "X-Tenant-Id: $TENANT")

echo "[1/10] health"
curl -s "$BASE/health" | jq .

echo "[2/10] catalog"
curl -s "$BASE/v1/catalog" "${hdr[@]}" | jq '.items|length'

echo "[3/10] packs"
curl -s "$BASE/v1/catalog/packs" "${hdr[@]}" | jq .

echo "[4/10] create engagement"
ENG=$(curl -s -X POST "$BASE/v1/engagements" "${hdr[@]}" -H 'Content-Type: application/json' \
  -d '{"name":"Demo Net","tenant_id":"'"$TENANT"'","type":"network","scope":{"in_scope_domains":["example.com"],"in_scope_cidrs":["10.0.0.0/24"],"out_of_scope":[],"risk_tier":"safe_active","windows":[]}}' | jq -r .id)
echo "ENG=$ENG"

echo "[5/10] validate selection"
cat > sel.json <<'JSON'
{"selected_tests":[{"id":"network.discovery.ping_sweep"},{"id":"network.nmap.tcp_top_1000"}],"agents":{"strategy":"recommended"},"risk_tier":"safe_active"}
JSON
curl -s -X POST "$BASE/v2/engagements/$ENG/plan/validate" "${hdr[@]}" -H 'Content-Type: application/json' --data-binary @sel.json | jq .

echo "[6/10] create plan"
PLAN=$(curl -s -X POST "$BASE/v1/engagements/$ENG/plan" "${hdr[@]}" -H 'Content-Type: application/json' --data-binary @sel.json | jq -r .id)
echo "PLAN=$PLAN"

echo "[7/10] start run"
RUN=$(curl -s -X POST "$BASE/v1/tests" "${hdr[@]}" -H 'Content-Type: application/json' -d '{"engagement_id":"'"$ENG"'","plan_id":"'"$PLAN"'"}' | jq -r .id)
echo "RUN=$RUN"

echo "[8/10] pause/resume"
curl -s -X POST "$BASE/v2/runs/$RUN/control" "${hdr[@]}" -H 'Content-Type: application/json' -d '{"action":"pause"}' | jq .
sleep 1
curl -s -X POST "$BASE/v2/runs/$RUN/control" "${hdr[@]}" -H 'Content-Type: application/json' -d '{"action":"resume"}' | jq .

echo "[9/10] ingest findings"
cat > findings.json <<'JSON'
[{"title":"Directory listing enabled","severity":"low","description":"Autoindex on /static","assets":{"urls":["https://app.example.com/static/"]},"recommendation":"Disable autoindex","tags":{"owasp":["A5-2021"],"cwe":[548]}}]
JSON
curl -s -X POST "$BASE/v2/runs/$RUN/findings" "${hdr[@]}" -H 'Content-Type: application/json' --data-binary @findings.json | jq .

echo "[10/10] export report.md"
curl -s "$BASE/v2/reports/run/$RUN.md" "${hdr[@]}" -o report.md
echo "OK — report.md written"
