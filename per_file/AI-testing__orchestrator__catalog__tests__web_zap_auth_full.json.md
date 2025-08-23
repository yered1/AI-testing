# File: AI-testing/orchestrator/catalog/tests/web_zap_auth_full.json

- Size: 785 bytes
- Kind: text
- SHA256: 28ad10cf0b581548128884f4a0faa6d6a4f20583f92e3087285a67435cf831be

## Head (first 60 lines)

```
{
  "id": "web_zap_auth_full",
  "title": "Web \u2014 ZAP Authenticated Full Scan",
  "category": "web",
  "description": "Authenticated active scan via ZAP (intrusive). Requires credentials and approval.",
  "tool_adapter": "web_zap_auth_full",
  "params_schema": {
    "type": "object",
    "properties": {
      "target": {
        "type": "string"
      },
      "login_url": {
        "type": "string"
      },
      "username": {
        "type": "string"
      },
      "password": {
        "type": "string"
      },
      "user_field": {
        "type": "string",
        "default": "username"
      },
      "pass_field": {
        "type": "string",
        "default": "password"
      }
    },
    "required": [
      "target",
      "username",
      "password"
    ]
  }
}
```

