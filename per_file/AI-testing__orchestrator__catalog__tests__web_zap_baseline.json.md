# File: AI-testing/orchestrator/catalog/tests/web_zap_baseline.json

- Size: 518 bytes
- Kind: text
- SHA256: f806ada29223ec30f003ea9af23aca013bc76f1a8516daf7bbdca55d14c0a0e3

## Head (first 60 lines)

```
{
  "id": "web_zap_baseline",
  "title": "Web \u2014 OWASP ZAP Baseline",
  "category": "web",
  "description": "Non-intrusive baseline scan via OWASP ZAP (passive + light spider).",
  "tool_adapter": "zap_baseline",
  "params_schema": {
    "type": "object",
    "properties": {
      "domains": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "mode": {
        "type": "string",
        "enum": [
          "baseline",
          "full"
        ]
      }
    }
  }
}
```

