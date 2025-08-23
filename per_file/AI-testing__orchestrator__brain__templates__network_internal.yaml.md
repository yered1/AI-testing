# File: AI-testing/orchestrator/brain/templates/network_internal.yaml

- Size: 368 bytes
- Kind: text
- SHA256: dcbd08153be492692ef8b983fddab6c0b199d0317b7654278f6bf2adc4b2b0d0

## Head (first 60 lines)

```
defaults:
  tests:
    - network_discovery_ping_sweep
    - network_nmap_tcp_full
    - network_nmap_udp_top_200
params:
  network_discovery_ping_sweep:
    cidrs: "{{ scope.in_scope_cidrs | default([]) }}"
  network_nmap_tcp_full:
    cidrs: "{{ scope.in_scope_cidrs | default([]) }}"
  network_nmap_udp_top_200:
    cidrs: "{{ scope.in_scope_cidrs | default([]) }}"
```

