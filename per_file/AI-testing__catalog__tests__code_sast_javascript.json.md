# File: AI-testing/catalog/tests/code_sast_javascript.json

- Size: 640 bytes
- Kind: text
- SHA256: 2fe836fe6315173d97e2fb76b6c9d53192dd3fbc140ddb5e76e0bde197dbb21f

## Head (first 60 lines)

```
{
  "id": "code.sast.javascript",
  "name": "SAST: JavaScript/TypeScript",
  "category": "Code",
  "risk_tier": "recon",
  "description": "Static analysis for JS/TS; security smells and secrets.",
  "prerequisites": [],
  "exclusive_with": [],
  "requires": {
    "agents": [
      "kali_gateway",
      "cross_platform"
    ],
    "capabilities": [],
    "inputs": [
      "repo_url|zip"
    ]
  },
  "optional_inputs": [],
  "estimator": {
    "time_per_host_sec": 45,
    "cost_units": 3
  },
  "outputs": [
    "sarif"
  ],
  "tool_adapter": "sast-js@0.3.0",
  "evidence_retention": "standard",
  "policy_tags": [
    "code-only"
  ]
}
```

