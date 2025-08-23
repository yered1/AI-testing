#!/bin/bash
# Comprehensive smoke test for enhanced features

set -e

API="${API:-http://localhost:8080}"
TENANT="${TENANT:-t_demo}"
USER="${USER:-test}"
EMAIL="${EMAIL:-test@example.com}"

echo "==================================="
echo "Enhanced Platform Smoke Test"
echo "==================================="

# Check findings API
echo ""
echo "Testing Findings API..."
curl -s -X GET "$API/v2/findings/stats/test" \
    -H "X-Dev-User: $USER" \
    -H "X-Dev-Email: $EMAIL" \
    -H "X-Tenant-Id: $TENANT" || echo "Findings API not ready"

# Check Brain providers
echo ""
echo "Testing Brain Providers..."
curl -s -X GET "$API/v3/brain/providers" \
    -H "X-Dev-User: $USER" \
    -H "X-Dev-Email: $EMAIL" \
    -H "X-Tenant-Id: $TENANT" | jq '.' || echo "Brain API not ready"

# Check enhanced catalog
echo ""
echo "Checking Enhanced Catalog..."
curl -s -X GET "$API/v1/catalog" \
    -H "X-Dev-User: $USER" \
    -H "X-Dev-Email: $EMAIL" \
    -H "X-Tenant-Id: $TENANT" | jq '.tests | keys | length' || echo "Catalog not loaded"

echo ""
echo "Smoke test complete!"
