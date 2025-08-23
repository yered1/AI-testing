# File: AI-testing/catalog/tests/api_auth_fuzz.json

- Size: 718 bytes
- Kind: text
- SHA256: 72df3ec63538f0ee10bfbc8c49ea7ff838b7f0dad9f0a8683aedd2729bbb9aab

## Head (first 60 lines)

```
{
  "id": "api.auth.fuzz",
  "name": "API: AuthZ Fuzz",
  "category": "API",
  "risk_tier": "safe_active",
  "description": "Tests for broken object-level authorization via crafted requests.",
  "prerequisites": [
    "api.schema.conformance"
  ],
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
  "optional_inputs": [
    {
      "key": "token_ref",
      "type": "string"
    }
  ],
  "estimator": {
    "time_per_host_sec": 240,
    "cost_units": 6
  },
  "outputs": [
    "api_findings"
  ],
  "tool_adapter": "api-authz-fuzzer@0.2.0",
  "evidence_retention": "standard",
  "policy_tags": []
}
```

