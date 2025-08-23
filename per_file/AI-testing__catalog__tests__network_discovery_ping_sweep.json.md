# File: AI-testing/catalog/tests/network_discovery_ping_sweep.json

- Size: 744 bytes
- Kind: text
- SHA256: 3de196a1902167d8bd84f9b2b414c036573d1f57c101dc6ed124721938de89d6

## Head (first 60 lines)

```
{
  "id": "network.discovery.ping_sweep",
  "name": "Host Discovery (ICMP/ARP)",
  "category": "Network",
  "risk_tier": "recon",
  "description": "Discover live hosts in-scope via ICMP/ARP.",
  "prerequisites": [],
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
      "key": "rate_limit_rps",
      "type": "number",
      "min": 1,
      "max": 200,
      "default": 50
    }
  ],
  "estimator": {
    "time_per_host_sec": 5,
    "cost_units": 1
  },
  "outputs": [
    "hosts"
  ],
  "tool_adapter": "kalitool-fping@1.0.0",
  "evidence_retention": "short",
  "policy_tags": [
    "scoped-network-only"
  ]
}
```

