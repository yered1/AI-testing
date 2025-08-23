# File: AI-testing/catalog/tests/network_nmap_tcp_top_1000.json

- Size: 1008 bytes
- Kind: text
- SHA256: efe07bfe634627ea27a2500331f2acfd753bf120c0bad82030b10b06152deac9

## Head (first 60 lines)

```
{
  "id": "network.nmap.tcp_top_1000",
  "name": "Nmap TCP Top 1000",
  "category": "Network",
  "risk_tier": "safe_active",
  "description": "Fast TCP scan of common ports with service/version detection.",
  "prerequisites": [
    "network.discovery.ping_sweep"
  ],
  "exclusive_with": [
    "network.nmap.full_connect_all_ports"
  ],
  "requires": {
    "agents": [
      "kali_gateway"
    ],
    "capabilities": [
      "net_raw"
    ],
    "inputs": []
  },
  "optional_inputs": [
    {
      "key": "rate_limit_rps",
      "type": "number",
      "min": 1,
      "max": 200,
      "default": 20
    },
    {
      "key": "top_ports",
      "type": "number",
      "enum": [
        100,
        1000
      ],
      "default": 1000
    }
  ],
  "estimator": {
    "time_per_host_sec": 45,
    "cost_units": 2
  },
  "outputs": [
    "ports",
    "services",
    "banners"
  ],
  "tool_adapter": "kalitool-nmap@1.4.2",
  "evidence_retention": "short",
  "policy_tags": [
    "scoped-network-only"
  ]
}
```

