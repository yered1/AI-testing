# File: AI-testing/orchestrator/catalog/tests/tests.json.bak

- Size: 15458 bytes
- Kind: text
- SHA256: 4c6cfab227b07bb9840d4cd5481eac7b2243363b823da1e07e702ca77459e3e9

## Head (first 60 lines)

```
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
    "tags": [
      "network",
      "discovery",
      "nmap",
      "ports"
    ],
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
    "tags": [
      "network",
      "discovery",
      "nmap",
      "comprehensive"
    ]
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
    "tags": [
      "network",
      "discovery",
      "nmap",
      "udp"
    ]
  },
  "network_dnsx_resolve": {
    "id": "network_dnsx_resolve",
    "name": "DNS Resolution",
    "description": "Resolve DNS records using dnsx",
```

## Tail (last 60 lines)

```
    "agent_type": "red_team_agent",
    "risk_level": "high",
    "requires_approval": true,
    "estimated_duration": 1200,
    "tags": [
      "exfiltration",
      "dlp",
      "data_loss",
      "red_team"
    ]
  },
  "persistence_mechanisms": {
    "id": "persistence_mechanisms",
    "name": "Persistence Mechanism Testing",
    "description": "Test ability to establish persistence on compromised systems",
    "category": "Red Team",
    "agent_type": "red_team_agent",
    "risk_level": "critical",
    "requires_approval": true,
    "estimated_duration": 900,
    "tags": [
      "persistence",
      "backdoor",
      "red_team",
      "apt"
    ]
  },
  "edr_evasion_test": {
    "id": "edr_evasion_test",
    "name": "EDR/AV Evasion Testing",
    "description": "Test endpoint detection and response evasion techniques",
    "category": "Red Team",
    "agent_type": "evasion_agent",
    "risk_level": "high",
    "requires_approval": true,
    "estimated_duration": 1500,
    "tags": [
      "evasion",
      "edr",
      "antivirus",
      "bypass"
    ]
  },
  "physical_security_assessment": {
    "id": "physical_security_assessment",
    "name": "Physical Security Assessment",
    "description": "Test physical security controls (locks, badges, tailgating)",
    "category": "Physical Security",
    "agent_type": "physical_agent",
    "risk_level": "high",
    "requires_approval": true,
    "estimated_duration": 7200,
    "tags": [
      "physical",
      "locks",
      "badges",
      "access_control"
    ]
  }
}
```

