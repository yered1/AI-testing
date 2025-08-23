# File: AI-testing/schemas/finding.schema.json

- Size: 903 bytes
- Kind: text
- SHA256: 7a9f2cac673767bae344445857c666c27e1aa5a36d71fa0c4f7f6d2d45714cb4

## Head (first 60 lines)

```
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Finding",
  "type": "object",
  "required": [
    "id",
    "engagement_id",
    "severity",
    "title",
    "evidence"
  ],
  "properties": {
    "id": {
      "type": "string"
    },
    "engagement_id": {
      "type": "string"
    },
    "asset_id": {
      "type": "string"
    },
    "severity": {
      "type": "string",
      "enum": [
        "Info",
        "Low",
        "Medium",
        "High",
        "Critical"
      ]
    },
    "cwe": {
      "type": "string"
    },
    "cve": {
      "type": "string"
    },
    "title": {
      "type": "string"
    },
    "description": {
      "type": "string"
    },
    "recommendation": {
      "type": "string"
    },
    "evidence": {
      "type": "array",
      "items": {
        "type": "object"
      }
    },
    "trace": {
      "type": "object"
    }
  }
}
```

