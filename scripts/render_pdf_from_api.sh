#!/usr/bin/env bash
set -euo pipefail
RUN_ID="${1:-}"
if [ -z "$RUN_ID" ]; then
  echo "Usage: $0 <RUN_ID>"
  exit 1
fi
API="${API:-http://localhost:8080}"
REPORTER="${REPORTER:-http://localhost:8082}"
TENANT="${TENANT:-t_demo}"
HDR=(-H "X-Dev-User: yered" -H "X-Dev-Email: yered@example.com" -H "X-Tenant-Id: ${TENANT}")
HTML=$(curl -s "$API/v2/reports/run/$RUN_ID.html" "${HDR[@]}")
curl -s -X POST "$REPORTER/render/pdf" -H "Content-Type: application/json" -d "$(jq -Rs --arg title "run-$RUN_ID" '{html: ., title: $title}')" <<<'$HTML' -o "report_$RUN_ID.pdf"
echo "Saved report_$RUN_ID.pdf"
