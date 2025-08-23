# File: AI-testing/scripts/fix_catalog_script.sh

- Size: 9251 bytes
- Kind: text
- SHA256: 822d5f79db9031d600c51f50f13698ef38d096cf836b32d6998882fa47d35f6e

## Head (first 60 lines)

```
#!/bin/bash
# Fix catalog directory structure and setup

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "==================================="
echo "Fixing Catalog Structure"
echo "==================================="

# Create catalog directory structure
echo "Creating catalog directories..."
mkdir -p "${PROJECT_ROOT}/orchestrator/catalog/tests"
mkdir -p "${PROJECT_ROOT}/orchestrator/catalog/packs"

# Create base catalog files
echo "Creating base catalog files..."

# Base tests catalog
cat > "${PROJECT_ROOT}/orchestrator/catalog/tests/tests.json" << 'EOF'
{
  "network_nmap_tcp_top_1000": {
    "id": "network_nmap_tcp_top_1000",
    "name": "Nmap TCP Top 1000 Ports",
    "description": "Scan top 1000 TCP ports using nmap",
    "category": "Network Discovery",
    "agent_type": "kali_os",
    "risk_level": "low",
    "requires_approval": false,
    "estimated_duration": 300,
    "tags": ["network", "discovery", "nmap", "ports"],
    "params": {
      "target": {
        "type": "string",
        "required": true,
        "description": "Target IP or hostname"
      }
    }
  },
  "network_nmap_tcp_full": {
    "id": "network_nmap_tcp_full",
    "name": "Nmap Full TCP Scan",
    "description": "Full TCP port scan (all 65535 ports)",
    "category": "Network Discovery",
    "agent_type": "kali_os",
    "risk_level": "medium",
    "requires_approval": true,
    "estimated_duration": 3600,
    "tags": ["network", "discovery", "nmap", "comprehensive"]
  },
  "network_nmap_udp_top_200": {
    "id": "network_nmap_udp_top_200",
    "name": "Nmap UDP Top 200 Ports",
    "description": "Scan top 200 UDP ports",
    "category": "Network Discovery",
    "agent_type": "kali_os",
    "risk_level": "medium",
    "requires_approval": false,
```

## Tail (last 60 lines)

```
  },
  "default_external_min": {
    "id": "default_external_min",
    "name": "Minimal External Assessment",
    "description": "Quick external assessment",
    "tests": [
      "network_dnsx_resolve",
      "web_httpx_probe",
      "network_nmap_tcp_top_1000"
    ],
    "estimated_duration": 480,
    "risk_level": "low",
    "tags": ["external", "quick"]
  },
  "default_remote_kali_min": {
    "id": "default_remote_kali_min",
    "name": "Remote Kali Minimum",
    "description": "Basic remote Kali testing",
    "tests": [
      "remote_kali_nmap_tcp_top_1000"
    ],
    "estimated_duration": 300,
    "risk_level": "low",
    "tags": ["remote", "kali"]
  }
}
EOF

echo "✓ Catalog structure created"

# Now merge enhanced tests if they exist
if [ -f "${PROJECT_ROOT}/orchestrator/catalog/tests/enhanced_tests.json" ]; then
    echo "Merging enhanced tests..."
    if command -v jq &> /dev/null; then
        jq -s '.[0] * .[1]' \
            "${PROJECT_ROOT}/orchestrator/catalog/tests/tests.json" \
            "${PROJECT_ROOT}/orchestrator/catalog/tests/enhanced_tests.json" \
            > "${PROJECT_ROOT}/orchestrator/catalog/tests/tests_merged.json"
        mv "${PROJECT_ROOT}/orchestrator/catalog/tests/tests_merged.json" \
           "${PROJECT_ROOT}/orchestrator/catalog/tests/tests.json"
        echo "✓ Enhanced tests merged"
    fi
fi

if [ -f "${PROJECT_ROOT}/orchestrator/catalog/packs/enhanced_packs.json" ]; then
    echo "Merging enhanced packs..."
    if command -v jq &> /dev/null; then
        jq -s '.[0] * .[1]' \
            "${PROJECT_ROOT}/orchestrator/catalog/packs/packs.json" \
            "${PROJECT_ROOT}/orchestrator/catalog/packs/enhanced_packs.json" \
            > "${PROJECT_ROOT}/orchestrator/catalog/packs/packs_merged.json"
        mv "${PROJECT_ROOT}/orchestrator/catalog/packs/packs_merged.json" \
           "${PROJECT_ROOT}/orchestrator/catalog/packs/packs.json"
        echo "✓ Enhanced packs merged"
    fi
fi

echo ""
echo "Catalog setup complete!"
echo "You can now run: bash scripts/enable_enhanced_features.sh"
```

