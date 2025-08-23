# File: AI-testing/schemas/test-catalog-item.schema.json

- Size: 2109 bytes
- Kind: text
- SHA256: e409e7b12b887ff86ebd01f5079eb2d8216d7b0cfbb14dc02a21dc5bd5efc3a1

## Head (first 60 lines)

```
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TestCatalogItem",
  "type": "object",
  "required": [
    "id",
    "name",
    "category",
    "risk_tier",
    "description",
    "requires",
    "estimator",
    "tool_adapter"
  ],
  "properties": {
    "id": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "category": {
      "type": "string",
      "enum": [
        "Network",
        "Web",
        "API",
        "Mobile",
        "Code",
        "Cloud"
      ]
    },
    "risk_tier": {
      "type": "string",
      "enum": [
        "recon",
        "safe_active",
        "intrusive",
        "exploit_proof_only"
      ]
    },
    "description": {
      "type": "string"
    },
    "prerequisites": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "exclusive_with": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "requires": {
      "type": "object",
      "properties": {
        "agents": {
```

## Tail (last 60 lines)

```
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "capabilities": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "inputs": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    },
    "optional_inputs": {
      "type": "array",
      "items": {
        "type": "object"
      }
    },
    "estimator": {
      "type": "object",
      "required": [
        "time_per_host_sec",
        "cost_units"
      ],
      "properties": {
        "time_per_host_sec": {
          "type": "number"
        },
        "cost_units": {
          "type": "number"
        }
      }
    },
    "outputs": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "tool_adapter": {
      "type": "string"
    },
    "evidence_retention": {
      "type": "string"
    },
    "policy_tags": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

