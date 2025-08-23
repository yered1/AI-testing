# File: AI-testing/orchestrator/ui/templates/brain_builder.html

- Size: 1168 bytes
- Kind: text
- SHA256: 2e7c537ad8e3355a2bfacb9f4f717b6411a04173e9ebdf38f086b2a6658a0e80

## Head (first 60 lines)

```
{% extends "base.html" %}
{% block content %}
<h2>Brain Planner (v3)</h2>
<div class="card">
  <label>Tenant</label>
  <input id="tenant" placeholder="t_demo" />
  <label>Engagement Type</label>
  <select id="etype">
    <option>web</option><option>network</option><option>code</option><option>mobile</option>
  </select>
  <label>Domains (comma)</label>
  <input id="domains" placeholder="example.com, www.example.com" />
  <label>CIDRs (comma)</label>
  <input id="cidrs" placeholder="10.0.0.0/24" />
  <label>Provider</label>
  <select id="provider">
    <option value="heuristic">heuristic (default)</option>
    <option value="openai_chat">openai_chat</option>
    <option value="anthropic">anthropic</option>
    <option value="azure_openai">azure_openai</option>
  </select>
  <label><input type="checkbox" id="allow_intrusive"> Allow intrusive</label>
  <button id="btnPlan">Plan</button>
</div>
<pre id="planOut" class="mono"></pre>
<div class="card">
  <button id="btnValidate">Validate</button>
  <button id="btnCreatePlan">Create Plan</button>
  <button id="btnStartRun">Start Run</button>
</div>
<script src="/ui/static/brain.js"></script>
{% endblock %}
```

