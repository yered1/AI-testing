# File: AI-testing/orchestrator/catalog/tests/code_semgrep_default.json

- Size: 463 bytes
- Kind: text
- SHA256: 18b93d4572c1fa3c5b615ee4e34ec8afc8b378659fa18b803b6e5145024a0250

## Head (first 60 lines)

```
{
  "id": "code_semgrep_default",
  "title": "Code \u2014 Semgrep (default ruleset)",
  "category": "code",
  "description": "Run Semgrep with default 'p/ci' rules on uploaded source package (zip/tar).",
  "tool_adapter": "semgrep_default",
  "params_schema": {
    "type": "object",
    "properties": {
      "config": {
        "type": "string",
        "description": "Semgrep config, e.g. p/ci, p/owasp-top-ten",
        "default": "p/ci"
      }
    }
  }
}
```

