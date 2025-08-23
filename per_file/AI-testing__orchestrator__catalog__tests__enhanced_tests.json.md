# File: AI-testing/orchestrator/catalog/tests/enhanced_tests.json

- Size: 9935 bytes
- Kind: text
- SHA256: 5a753af64be48cff1b701ee13f60d58a239452a26a16f8ffa1ea068093a2be1e

## Head (first 60 lines)

```
{
  "cloud_aws_audit": {
    "id": "cloud_aws_audit",
    "name": "AWS Cloud Security Audit",
    "description": "Comprehensive AWS cloud configuration and security audit using ScoutSuite and custom checks",
    "category": "Cloud Security",
    "agent_type": "cloud_aws",
    "risk_level": "low",
    "requires_approval": false,
    "estimated_duration": 900,
    "tags": ["cloud", "aws", "audit", "configuration"],
    "params": {
      "services": {
        "type": "array",
        "default": ["iam", "ec2", "s3", "rds", "cloudtrail"],
        "description": "AWS services to audit"
      },
      "use_scoutsuite": {
        "type": "boolean",
        "default": true,
        "description": "Use ScoutSuite for comprehensive scanning"
      },
      "custom_checks": {
        "type": "boolean",
        "default": true,
        "description": "Run custom security checks"
      }
    }
  },
  "cloud_azure_audit": {
    "id": "cloud_azure_audit",
    "name": "Azure Cloud Security Audit",
    "description": "Azure cloud configuration and security assessment",
    "category": "Cloud Security",
    "agent_type": "cloud_azure",
    "risk_level": "low",
    "requires_approval": false,
    "estimated_duration": 900,
    "tags": ["cloud", "azure", "audit", "configuration"]
  },
  "cloud_gcp_audit": {
    "id": "cloud_gcp_audit",
    "name": "GCP Cloud Security Audit",
    "description": "Google Cloud Platform security assessment",
    "category": "Cloud Security",
    "agent_type": "cloud_gcp",
    "risk_level": "low",
    "requires_approval": false,
    "estimated_duration": 900,
    "tags": ["cloud", "gcp", "audit", "configuration"]
  },
  "exploit_vulnerability": {
    "id": "exploit_vulnerability",
    "name": "Automated Vulnerability Exploitation",
    "description": "Attempt to exploit discovered vulnerabilities using Metasploit",
    "category": "Exploitation",
    "agent_type": "exploitation",
    "risk_level": "critical",
    "requires_approval": true,
    "estimated_duration": 1800,
```

## Tail (last 60 lines)

```
    "requires_approval": false,
    "estimated_duration": 1800,
    "tags": ["blockchain", "smart_contract", "ethereum", "solidity"]
  },
  "ransomware_simulation": {
    "id": "ransomware_simulation",
    "name": "Ransomware Attack Simulation",
    "description": "Simulate ransomware attack patterns (safe mode)",
    "category": "Red Team",
    "agent_type": "red_team_agent",
    "risk_level": "critical",
    "requires_approval": true,
    "estimated_duration": 3600,
    "tags": ["ransomware", "simulation", "red_team", "incident_response"]
  },
  "data_exfiltration_test": {
    "id": "data_exfiltration_test",
    "name": "Data Exfiltration Testing",
    "description": "Test data loss prevention and exfiltration detection",
    "category": "Red Team",
    "agent_type": "red_team_agent",
    "risk_level": "high",
    "requires_approval": true,
    "estimated_duration": 1200,
    "tags": ["exfiltration", "dlp", "data_loss", "red_team"]
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
    "tags": ["persistence", "backdoor", "red_team", "apt"]
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
    "tags": ["evasion", "edr", "antivirus", "bypass"]
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
    "tags": ["physical", "locks", "badges", "access_control"]
  }
}
```

