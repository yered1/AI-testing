# File: AI-testing/orchestrator/catalog/packs/packs.json

- Size: 8122 bytes
- Kind: text
- SHA256: 8abd76ab4bf23b7b6b2121c9e5e1524056bf2bafca0e67ffaf202e76b5e61251

## Head (first 60 lines)

```
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
    "tags": [
      "web",
      "discovery"
    ]
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
    "tags": [
      "web",
      "active"
    ]
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
    "tags": [
      "network",
      "discovery"
    ]
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
    "tags": [
      "network",
      "internal",
```

## Tail (last 60 lines)

```
  },
  "compliance_baseline": {
    "id": "compliance_baseline",
    "name": "Compliance Baseline Assessment",
    "description": "Non-intrusive compliance-focused security assessment",
    "tests": [
      "network_nmap_tcp_top_1000",
      "web_zap_baseline",
      "cloud_aws_audit",
      "container_security_scan",
      "supply_chain_analysis"
    ],
    "estimated_duration": 3600,
    "risk_level": "low",
    "tags": [
      "compliance",
      "baseline",
      "non_intrusive",
      "audit"
    ]
  },
  "quick_recon": {
    "id": "quick_recon",
    "name": "Quick Reconnaissance",
    "description": "Fast reconnaissance and enumeration pack",
    "tests": [
      "network_dnsx_resolve",
      "web_httpx_probe",
      "network_nmap_tcp_top_1000"
    ],
    "estimated_duration": 1200,
    "risk_level": "low",
    "tags": [
      "recon",
      "quick",
      "discovery",
      "enumeration"
    ]
  },
  "zero_trust_validation": {
    "id": "zero_trust_validation",
    "name": "Zero Trust Architecture Validation",
    "description": "Validate zero trust security controls and segmentation",
    "tests": [
      "network_nmap_tcp_full",
      "active_directory_enum",
      "api_security_test",
      "credential_harvesting",
      "data_exfiltration_test"
    ],
    "estimated_duration": 7200,
    "risk_level": "high",
    "tags": [
      "zero_trust",
      "segmentation",
      "validation",
      "architecture"
    ]
  }
}
```

