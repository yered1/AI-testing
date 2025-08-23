# File: AI-testing/catalog/packs/pack_standard_network.json

- Size: 252 bytes
- Kind: text
- SHA256: 61d648bb91fdf967fb6597e42f8128c11c6124ee63e88ca46ae77eef2418e37e

## Head (first 60 lines)

```
{
  "id": "pack.standard_network",
  "name": "Standard Network (safe)",
  "description": "Recommended safe network discovery & enumeration",
  "tests": [
    "network.discovery.ping_sweep",
    "network.nmap.tcp_top_1000",
    "network.enum.smb"
  ]
}
```

