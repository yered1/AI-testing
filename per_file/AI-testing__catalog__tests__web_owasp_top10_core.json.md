# File: AI-testing/catalog/tests/web_owasp_top10_core.json

- Size: 816 bytes
- Kind: text
- SHA256: 7d88e3d935fb9294538a5655a54cabac6fcd88491f162e951dad2fe302d9b93d

## Head (first 60 lines)

```
{
  "id": "web.owasp.top10.core",
  "name": "Web: OWASP Top 10 Core",
  "category": "Web",
  "risk_tier": "safe_active",
  "description": "Run core checks for OWASP Top 10.",
  "prerequisites": [],
  "exclusive_with": [],
  "requires": {
    "agents": [
      "kali_gateway"
    ],
    "capabilities": [],
    "inputs": [
      "url"
    ]
  },
  "optional_inputs": [
    {
      "key": "auth_ref",
      "type": "string"
    },
    {
      "key": "max_requests_per_min",
      "type": "number",
      "min": 10,
      "max": 600,
      "default": 120
    }
  ],
  "estimator": {
    "time_per_host_sec": 180,
    "cost_units": 5
  },
  "outputs": [
    "http_findings",
    "screenshots"
  ],
  "tool_adapter": "kalitool-zap@2.0.0",
  "evidence_retention": "standard",
  "policy_tags": [
    "respect-robots"
  ]
}
```

