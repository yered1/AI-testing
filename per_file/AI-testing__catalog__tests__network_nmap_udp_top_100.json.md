# File: AI-testing/catalog/tests/network_nmap_udp_top_100.json

- Size: 804 bytes
- Kind: text
- SHA256: 20e86a0ded3b28984f4ced02ad9c1b0882a0d792c9ca4e5dc2545b645bd9a57f

## Head (first 60 lines)

```
{
  "id": "network.nmap.udp_top_100",
  "name": "Nmap UDP Top 100",
  "category": "Network",
  "risk_tier": "safe_active",
  "description": "Nmap UDP scan for common ports.",
  "prerequisites": [
    "network.discovery.ping_sweep"
  ],
  "exclusive_with": [],
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
      "key": "top_ports",
      "type": "number",
      "enum": [
        50,
        100,
        250
      ],
      "default": 100
    }
  ],
  "estimator": {
    "time_per_host_sec": 90,
    "cost_units": 2
  },
  "outputs": [
    "ports",
    "services"
  ],
  "tool_adapter": "kalitool-nmap@1.4.2",
  "evidence_retention": "short",
  "policy_tags": [
    "scoped-network-only"
  ]
}
```

