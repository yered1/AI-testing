# File: AI-testing/orchestrator/brain/templates/web.yaml

- Size: 353 bytes
- Kind: text
- SHA256: ee21efe91a4acefa2398ff6eb8cd1e6255974d631db223d4dbe21a7231048e81

## Head (first 60 lines)

```
defaults:
  tests:
    - web_httpx_probe
    - web_zap_baseline
    - web_nuclei_default
params:
  web_httpx_probe:
    targets: "{{ scope.in_scope_domains | default([]) }}"
  web_zap_baseline:
    domains: "{{ scope.in_scope_domains | default([]) }}"
    mode: "baseline"
  web_nuclei_default:
    targets: "{{ scope.in_scope_domains | default([]) }}"
```

