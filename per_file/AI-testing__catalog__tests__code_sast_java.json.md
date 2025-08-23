# File: AI-testing/catalog/tests/code_sast_java.json

- Size: 716 bytes
- Kind: text
- SHA256: 4f483577356337fc823ca958c301c80e1c056987d266bf77e245c8dd201de40c

## Head (first 60 lines)

```
{
  "id": "code.sast.java",
  "name": "SAST: Java",
  "category": "Code",
  "risk_tier": "recon",
  "description": "Static analysis for Java codebases; secrets and insecure APIs.",
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
  "optional_inputs": [
    {
      "key": "ruleset",
      "type": "string",
      "default": "default"
    }
  ],
  "estimator": {
    "time_per_host_sec": 60,
    "cost_units": 3
  },
  "outputs": [
    "sarif"
  ],
  "tool_adapter": "sast-java@0.3.1",
  "evidence_retention": "standard",
  "policy_tags": [
    "code-only"
  ]
}
```

