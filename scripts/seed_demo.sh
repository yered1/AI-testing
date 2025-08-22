#!/usr/bin/env bash
set -euo pipefail
BASE=${BASE:-http://localhost:8080}
USER=${USER:-yered}
EMAIL=${EMAIL:-yered@example.com}
TENANT=${TENANT:-t_demo}
hdr=(-H "X-Dev-User: $USER" -H "X-Dev-Email: $EMAIL" -H "X-Tenant-Id: $TENANT")

ENG=$(curl -s -X POST "$BASE/v1/engagements" "${hdr[@]}" -H 'Content-Type: application/json' \
  -d '{"name":"Seed Engagement","tenant_id":"'"$TENANT"'","type":"network","scope":{"in_scope_domains":["example.com"],"in_scope_cidrs":["10.0.0.0/24"],"out_of_scope":[],"risk_tier":"safe_active","windows":[]}}' | jq -r .id)
echo "ENG=$ENG"
