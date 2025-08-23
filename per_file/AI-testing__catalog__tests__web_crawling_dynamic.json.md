# File: AI-testing/catalog/tests/web_crawling_dynamic.json

- Size: 703 bytes
- Kind: text
- SHA256: 13ac19857a4d77fb26e6850def429da42ca564bb2df2e9cb07fdf705abfba7b3

## Head (first 60 lines)

```
{
  "id": "web.crawling.dynamic",
  "name": "Web Dynamic Crawler",
  "category": "Web",
  "risk_tier": "recon",
  "description": "Dynamic site crawl to build URL inventory.",
  "prerequisites": [],
  "exclusive_with": [],
  "requires": {
    "agents": [
      "kali_gateway"
    ],
    "capabilities": [],
    "inputs": [
      "url"
    ]
  },
  "optional_inputs": [
    {
      "key": "max_depth",
      "type": "number",
      "min": 1,
      "max": 8,
      "default": 3
    }
  ],
  "estimator": {
    "time_per_host_sec": 120,
    "cost_units": 2
  },
  "outputs": [
    "urls",
    "screenshots"
  ],
  "tool_adapter": "kalitool-zap@2.0.0",
  "evidence_retention": "short",
  "policy_tags": []
}
```

