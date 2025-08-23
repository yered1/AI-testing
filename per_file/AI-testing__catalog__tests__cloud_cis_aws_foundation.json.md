# File: AI-testing/catalog/tests/cloud_cis_aws_foundation.json

- Size: 669 bytes
- Kind: text
- SHA256: 86675c1389a53a0ff5c8882ec296b4577a45381341cf75a7cd44ec2972c0742a

## Head (first 60 lines)

```
{
  "id": "cloud.cis.aws_foundation",
  "name": "Cloud: AWS CIS Foundations",
  "category": "Cloud",
  "risk_tier": "recon",
  "description": "Checks AWS account against CIS Foundations baseline (read-only).",
  "prerequisites": [],
  "exclusive_with": [],
  "requires": {
    "agents": [
      "cross_platform"
    ],
    "capabilities": [],
    "inputs": [
      "aws_role_arn|aws_access_key"
    ]
  },
  "optional_inputs": [],
  "estimator": {
    "time_per_host_sec": 180,
    "cost_units": 6
  },
  "outputs": [
    "cloud_findings"
  ],
  "tool_adapter": "cloud-audit-aws@0.1.0",
  "evidence_retention": "standard",
  "policy_tags": [
    "cloud-readonly"
  ]
}
```

