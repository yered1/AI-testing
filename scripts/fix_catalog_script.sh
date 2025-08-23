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
    "estimated_duration": 600,
    "tags": ["network", "discovery", "nmap", "udp"]
  },
  "network_dnsx_resolve": {
    "id": "network_dnsx_resolve",
    "name": "DNS Resolution",
    "description": "Resolve DNS records using dnsx",
    "category": "Discovery",
    "agent_type": "web_discovery",
    "risk_level": "low",
    "requires_approval": false,
    "estimated_duration": 60,
    "tags": ["dns", "discovery", "reconnaissance"]
  },
  "web_httpx_probe": {
    "id": "web_httpx_probe",
    "name": "HTTP Probe",
    "description": "Probe for HTTP/HTTPS services",
    "category": "Web Discovery",
    "agent_type": "web_discovery",
    "risk_level": "low",
    "requires_approval": false,
    "estimated_duration": 120,
    "tags": ["web", "discovery", "http"]
  },
  "web_zap_baseline": {
    "id": "web_zap_baseline",
    "name": "ZAP Baseline Scan",
    "description": "OWASP ZAP baseline scan (passive)",
    "category": "Web Application",
    "agent_type": "zap",
    "risk_level": "low",
    "requires_approval": false,
    "estimated_duration": 600,
    "tags": ["web", "zap", "owasp", "passive"]
  },
  "web_zap_auth_full": {
    "id": "web_zap_auth_full",
    "name": "ZAP Full Authenticated Scan",
    "description": "Full authenticated ZAP active scan",
    "category": "Web Application",
    "agent_type": "zap_auth",
    "risk_level": "high",
    "requires_approval": true,
    "estimated_duration": 1800,
    "tags": ["web", "zap", "owasp", "active", "authenticated"]
  },
  "web_nuclei_default": {
    "id": "web_nuclei_default",
    "name": "Nuclei Default Scan",
    "description": "Run Nuclei with default templates",
    "category": "Web Application",
    "agent_type": "nuclei",
    "risk_level": "low",
    "requires_approval": false,
    "estimated_duration": 900,
    "tags": ["web", "nuclei", "vulnerability"]
  },
  "code_semgrep_default": {
    "id": "code_semgrep_default",
    "name": "Semgrep Code Analysis",
    "description": "Static code analysis with Semgrep",
    "category": "Code Review",
    "agent_type": "semgrep",
    "risk_level": "low",
    "requires_approval": false,
    "estimated_duration": 300,
    "tags": ["code", "sast", "semgrep"]
  },
  "mobile_apk_static_default": {
    "id": "mobile_apk_static_default",
    "name": "APK Static Analysis",
    "description": "Static analysis of Android APK",
    "category": "Mobile",
    "agent_type": "mobile_apk",
    "risk_level": "low",
    "requires_approval": false,
    "estimated_duration": 600,
    "tags": ["mobile", "android", "apk", "static"]
  },
  "remote_kali_nmap_tcp_top_1000": {
    "id": "remote_kali_nmap_tcp_top_1000",
    "name": "Remote Kali Nmap Scan",
    "description": "Nmap scan via remote Kali agent",
    "category": "Network",
    "agent_type": "kali_remote",
    "risk_level": "low",
    "requires_approval": false,
    "estimated_duration": 300,
    "tags": ["network", "nmap", "remote"]
  },
  "remote_kali_run_tool": {
    "id": "remote_kali_run_tool",
    "name": "Run Tool on Remote Kali",
    "description": "Execute allowed tool on remote Kali",
    "category": "Custom",
    "agent_type": "kali_remote",
    "risk_level": "medium",
    "requires_approval": true,
    "estimated_duration": 600,
    "tags": ["remote", "custom", "tool"]
  }
}
EOF

# Base packs catalog
cat > "${PROJECT_ROOT}/orchestrator/catalog/packs/packs.json" << 'EOF'
{
  "default_web_discovery": {
    "id": "default_web_discovery",
    "name": "Web Discovery Pack",
    "description": "Basic web application discovery",
    "tests": [
      "network_dnsx_resolve",
      "web_httpx_probe"
    ],
    "estimated_duration": 180,
    "risk_level": "low",
    "tags": ["web", "discovery"]
  },
  "default_web_active": {
    "id": "default_web_active",
    "name": "Web Active Testing",
    "description": "Active web application testing",
    "tests": [
      "web_httpx_probe",
      "web_zap_baseline",
      "web_nuclei_default"
    ],
    "estimated_duration": 1620,
    "risk_level": "medium",
    "tags": ["web", "active"]
  },
  "default_network_discovery": {
    "id": "default_network_discovery",
    "name": "Network Discovery",
    "description": "Basic network discovery and enumeration",
    "tests": [
      "network_nmap_tcp_top_1000",
      "network_dnsx_resolve"
    ],
    "estimated_duration": 360,
    "risk_level": "low",
    "tags": ["network", "discovery"]
  },
  "default_internal_network": {
    "id": "default_internal_network",
    "name": "Internal Network Assessment",
    "description": "Comprehensive internal network testing",
    "tests": [
      "network_nmap_tcp_full",
      "network_nmap_udp_top_200"
    ],
    "estimated_duration": 4200,
    "risk_level": "high",
    "tags": ["network", "internal", "comprehensive"]
  },
  "default_code_review": {
    "id": "default_code_review",
    "name": "Code Review Pack",
    "description": "Static code analysis",
    "tests": [
      "code_semgrep_default"
    ],
    "estimated_duration": 300,
    "risk_level": "low",
    "tags": ["code", "sast"]
  },
  "default_mobile_static": {
    "id": "default_mobile_static",
    "name": "Mobile Static Analysis",
    "description": "Static analysis of mobile applications",
    "tests": [
      "mobile_apk_static_default"
    ],
    "estimated_duration": 600,
    "risk_level": "low",
    "tags": ["mobile", "static"]
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