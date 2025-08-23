# File: AI-testing/orchestrator/catalog/tests/remote_kali_nmap_tcp_top_1000.json

- Size: 426 bytes
- Kind: text
- SHA256: 0e132ffaaba996287f5018fcf344665143f29722caad28cc05fdc9c43a9c0c95

## Head (first 60 lines)

```
{
  "id": "remote_kali_nmap_tcp_top_1000",
  "title": "Remote Kali \u2014 Nmap TCP top 1000",
  "category": "network",
  "description": "Run nmap top 1000 TCP ports from the remote Kali agent.",
  "agent_kind": "kali_os",
  "tool_adapter": "nmap_tcp_top_1000",
  "params_schema": {
    "type": "object",
    "properties": {
      "target": {
        "type": "string"
      }
    },
    "required": [
      "target"
    ]
  }
}
```

