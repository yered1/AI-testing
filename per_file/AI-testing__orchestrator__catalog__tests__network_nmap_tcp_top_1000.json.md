# File: AI-testing/orchestrator/catalog/tests/network_nmap_tcp_top_1000.json

- Size: 413 bytes
- Kind: text
- SHA256: 7c123cc8d5166849aabaa776c13b1d4b228e6f54fb62471903c9d17574ac6481

## Head (first 60 lines)

```
{
  "id": "network_nmap_tcp_top_1000",
  "title": "Nmap \u2014 TCP top 1000",
  "category": "network",
  "description": "Nmap scan TCP top 1000 ports against in-scope hosts (rate-limited).",
  "tool_adapter": "nmap_tcp_top_1000",
  "params_schema": {
    "type": "object",
    "properties": {
      "targets": {
        "type": "array",
        "items": {
          "type": "string"
        }
      }
    }
  }
}
```

