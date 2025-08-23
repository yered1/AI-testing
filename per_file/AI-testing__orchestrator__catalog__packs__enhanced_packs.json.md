# File: AI-testing/orchestrator/catalog/packs/enhanced_packs.json

- Size: 5049 bytes
- Kind: text
- SHA256: 5e267df0eaf2b8ed33d79cdac627a21f6d0eea035dfee729c5123fc5ba9595fb

## Head (first 60 lines)

```
{
  "comprehensive_external": {
    "id": "comprehensive_external",
    "name": "Comprehensive External Assessment",
    "description": "Full external penetration test with discovery, scanning, and targeted exploitation",
    "tests": [
      "network_dnsx_resolve",
      "web_httpx_probe",
      "network_nmap_tcp_top_1000",
      "web_zap_baseline",
      "web_nuclei_default",
      "web_fuzzing_advanced",
      "api_security_test",
      "exploit_vulnerability"
    ],
    "estimated_duration": 7200,
    "risk_level": "high",
    "tags": ["external", "comprehensive", "full_test"]
  },
  "comprehensive_internal": {
    "id": "comprehensive_internal",
    "name": "Comprehensive Internal Assessment",
    "description": "Full internal network penetration test with AD enumeration and lateral movement",
    "tests": [
      "network_nmap_tcp_full",
      "network_nmap_udp_top_200",
      "active_directory_enum",
      "kerberos_attacks",
      "credential_harvesting",
      "privilege_escalation_check",
      "exploit_vulnerability",
      "persistence_mechanisms"
    ],
    "estimated_duration": 14400,
    "risk_level": "critical",
    "tags": ["internal", "comprehensive", "active_directory"]
  },
  "cloud_security_assessment": {
    "id": "cloud_security_assessment",
    "name": "Multi-Cloud Security Assessment",
    "description": "Security assessment across AWS, Azure, and GCP environments",
    "tests": [
      "cloud_aws_audit",
      "cloud_azure_audit",
      "cloud_gcp_audit",
      "container_security_scan",
      "supply_chain_analysis"
    ],
    "estimated_duration": 5400,
    "risk_level": "medium",
    "tags": ["cloud", "multi_cloud", "devsecops"]
  },
  "red_team_simulation": {
    "id": "red_team_simulation",
    "name": "Red Team Simulation",
    "description": "Full red team exercise with exploitation, persistence, and exfiltration",
    "tests": [
      "social_engineering_test",
      "exploit_vulnerability",
      "privilege_escalation_check",
```

## Tail (last 60 lines)

```
    "tags": ["devsecops", "cicd", "automation", "shift_left"]
  },
  "iot_ecosystem": {
    "id": "iot_ecosystem",
    "name": "IoT Ecosystem Assessment",
    "description": "Security assessment of IoT devices, protocols, and infrastructure",
    "tests": [
      "iot_device_assessment",
      "wireless_security_assessment",
      "network_nmap_tcp_full",
      "api_security_test"
    ],
    "estimated_duration": 5400,
    "risk_level": "high",
    "tags": ["iot", "embedded", "wireless", "industrial"]
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
    "tags": ["compliance", "baseline", "non_intrusive", "audit"]
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
    "tags": ["recon", "quick", "discovery", "enumeration"]
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
    "tags": ["zero_trust", "segmentation", "validation", "architecture"]
  }
}
```

