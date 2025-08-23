# File: AI-testing/catalog/tests/api_schema_conformance.json

- Size: 616 bytes
- Kind: text
- SHA256: 28105158b67a37286d84709072ba61ccd826156b45ba13905d55141e976edbed

## Head (first 60 lines)

```
{
  "id": "api.schema.conformance",
  "name": "API: Schema Conformance",
  "category": "API",
  "risk_tier": "safe_active",
  "description": "Check API conformance against OpenAPI spec.",
  "prerequisites": [],
  "exclusive_with": [],
  "requires": {
    "agents": [
      "kali_gateway"
    ],
    "capabilities": [],
    "inputs": [
      "openapi_url|openapi_file"
    ]
  },
  "optional_inputs": [],
  "estimator": {
    "time_per_host_sec": 120,
    "cost_units": 3
  },
  "outputs": [
    "api_findings"
  ],
  "tool_adapter": "api-oas-checker@0.1.0",
  "evidence_retention": "standard",
  "policy_tags": []
}
```

