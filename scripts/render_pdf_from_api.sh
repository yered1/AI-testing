#!/usr/bin/env bash
set -euo pipefail
API="${API:-http://localhost:8080}"
RUN_ID="${1:-}"
if [ -z "$RUN_ID" ]; then echo "Usage: $0 <run_id>"; exit 1; fi
TENANT="${TENANT:-t_demo}"
HDR=(-H "Content-Type: application/json" -H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")
HTML=$(curl -s "$API/v2/reports/run/$RUN_ID.html" "${HDR[@]}")
HEX=$(curl -s -X POST http://localhost:9090/render -H "Content-Type: application/json" -d "$(jq -n --arg html "$HTML" '{html:$html}')" | jq -r .pdf)
echo "$HEX" | xxd -r -p > "report_$RUN_ID.pdf"
echo "Saved report_$RUN_ID.pdf"
