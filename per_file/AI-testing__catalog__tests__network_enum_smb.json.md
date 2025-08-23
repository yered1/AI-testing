# File: AI-testing/catalog/tests/network_enum_smb.json

- Size: 641 bytes
- Kind: text
- SHA256: dcb7930184168bdff106815c3ef800b7f8e1484734f2da4b68ad5831ff578ed6

## Head (first 60 lines)

```
{
  "id": "network.enum.smb",
  "name": "SMB Enumeration",
  "category": "Network",
  "risk_tier": "safe_active",
  "description": "Enumerate SMB shares and users where exposed.",
  "prerequisites": [
    "network.nmap.tcp_top_1000"
  ],
  "exclusive_with": [],
  "requires": {
    "agents": [
      "kali_gateway"
    ],
    "capabilities": [],
    "inputs": []
  },
  "optional_inputs": [],
  "estimator": {
    "time_per_host_sec": 30,
    "cost_units": 2
  },
  "outputs": [
    "shares",
    "users"
  ],
  "tool_adapter": "kalitool-enum4linux@1.0.0",
  "evidence_retention": "short",
  "policy_tags": [
    "scoped-network-only"
  ]
}
```

