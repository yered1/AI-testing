# File: AI-testing/schemas/event.schema.json

- Size: 444 bytes
- Kind: text
- SHA256: cdd849dbd0bd2f704a50b2351bdf27da992501117a920f21edb11e0bcf071fb3

## Head (first 60 lines)

```
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventEnvelope",
  "type": "object",
  "required": [
    "type",
    "ts",
    "run_id"
  ],
  "properties": {
    "type": {
      "type": "string"
    },
    "ts": {
      "type": "string",
      "format": "date-time"
    },
    "run_id": {
      "type": "string"
    },
    "job_id": {
      "type": "string"
    },
    "payload": {
      "type": "object"
    }
  }
}
```

