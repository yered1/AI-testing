# File: AI-testing/catalog/tests/core.json

- Size: 631 bytes
- Kind: text
- SHA256: f6dedf86af9eeb0039deed32622ddb1e32400daea94cb2703b1df3e67ef77fa4

## Head (first 60 lines)

```
{
  "tests": [
    {
      "id": "web_discovery",
      "name": "Web Discovery",
      "agent": "zap",
      "risk": "safe"
    },
    {
      "id": "web_vulnerabilities",
      "name": "Web Vulnerability Scan",
      "agent": "zap",
      "risk": "moderate"
    },
    {
      "id": "nuclei_scan",
      "name": "Nuclei Templates",
      "agent": "nuclei",
      "risk": "safe"
    },
    {
      "id": "code_analysis",
      "name": "Static Code Analysis",
      "agent": "semgrep",
      "risk": "safe"
    },
    {
      "id": "port_scan",
      "name": "Port Scan",
      "agent": "nmap",
      "risk": "moderate"
    }
  ]
}
```

