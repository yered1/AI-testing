# File: AI-testing/schemas/plan.schema.json

- Size: 1494 bytes
- Kind: text
- SHA256: 554c5bbe96db545b9d24b5d6b117bc148b9c15d4b06746f19653b48ec37472a6

## Head (first 60 lines)

```
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PlanDSL",
  "type": "object",
  "required": [
    "engagement_id",
    "steps",
    "catalog_version"
  ],
  "properties": {
    "engagement_id": {
      "type": "string"
    },
    "catalog_version": {
      "type": "string"
    },
    "steps": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "id",
          "test_id",
          "tool_adapter",
          "risk_tier",
          "params"
        ],
        "properties": {
          "id": {
            "type": "string"
          },
          "test_id": {
            "type": "string"
          },
          "tool_adapter": {
            "type": "string"
          },
          "risk_tier": {
            "type": "string",
            "enum": [
              "recon",
              "safe_active",
              "intrusive",
              "exploit_proof_only",
              "post_ex"
            ]
          },
          "params": {
            "type": "object"
          },
          "agent_constraints": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "outputs": {
            "type": "array",
            "items": {
              "type": "string"
```

## Tail (last 60 lines)

```
    "catalog_version": {
      "type": "string"
    },
    "steps": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "id",
          "test_id",
          "tool_adapter",
          "risk_tier",
          "params"
        ],
        "properties": {
          "id": {
            "type": "string"
          },
          "test_id": {
            "type": "string"
          },
          "tool_adapter": {
            "type": "string"
          },
          "risk_tier": {
            "type": "string",
            "enum": [
              "recon",
              "safe_active",
              "intrusive",
              "exploit_proof_only",
              "post_ex"
            ]
          },
          "params": {
            "type": "object"
          },
          "agent_constraints": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "outputs": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "depends_on": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        }
      }
    }
  }
}
```

