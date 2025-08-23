# File: AI-testing/orchestrator/catalog/tests/remote_kali_run_tool.json

- Size: 556 bytes
- Kind: text
- SHA256: f42494445a6bca2e060aaeb5ffa8e12ddf223fbeca9a3b045a385f05326eb326

## Head (first 60 lines)

```
{
  "id": "remote_kali_run_tool",
  "title": "Remote Kali \u2014 Run tool (allowlist)",
  "category": "web",
  "description": "Execute an allowlisted tool on the remote Kali agent.",
  "agent_kind": "kali_os",
  "tool_adapter": "run_tool",
  "params_schema": {
    "type": "object",
    "properties": {
      "tool": {
        "type": "string"
      },
      "url": {
        "type": "string"
      },
      "target": {
        "type": "string"
      },
      "wordlist": {
        "type": "string"
      }
    },
    "required": [
      "tool"
    ]
  }
}
```

