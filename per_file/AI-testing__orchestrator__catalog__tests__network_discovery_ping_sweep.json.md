# File: AI-testing/orchestrator/catalog/tests/network_discovery_ping_sweep.json

- Size: 409 bytes
- Kind: text
- SHA256: 7f12b15d338f152c838d44eeb6fab7d5c040a3c5dceebea33f9e519bcee2d3b9

## Head (first 60 lines)

```
{
  "id": "network_discovery_ping_sweep",
  "title": "Network Discovery \u2014 Ping Sweep",
  "category": "network",
  "description": "Identify live hosts via ping sweep within in-scope CIDRs (safe).",
  "tool_adapter": "echo",
  "params_schema": {
    "type": "object",
    "properties": {
      "cidrs": {
        "type": "array",
        "items": {
          "type": "string"
        }
      }
    }
  }
}
```

