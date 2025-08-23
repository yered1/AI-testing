# File: AI-testing/orchestrator/catalog/tests/web_nuclei_default.json

- Size: 473 bytes
- Kind: text
- SHA256: 52b4643b09d797b89f3ed8dd2d2bbe4cdaacefe0892e4efcdce9a188a9ba0a3a

## Head (first 60 lines)

```
{
  "id": "web_nuclei_default",
  "title": "Web \u2014 Nuclei (default)",
  "category": "web",
  "description": "Run nuclei templates (severity: medium+).",
  "tool_adapter": "nuclei_default",
  "params_schema": {
    "type": "object",
    "properties": {
      "targets": {
        "type": "array",
        "items": {
          "type": "string"
        }
      },
      "severity": {
        "type": "string",
        "default": "medium,high,critical"
      }
    }
  }
}
```

