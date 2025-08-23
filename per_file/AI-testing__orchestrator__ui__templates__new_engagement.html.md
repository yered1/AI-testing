# File: AI-testing/orchestrator/ui/templates/new_engagement.html

- Size: 1499 bytes
- Kind: text
- SHA256: f87961e894713531c721035fb02c3a90cbdd010f05842422b9bf7a6a9148df44

## Head (first 60 lines)

```
{% extends "base.html" %}
{% block content %}
<section>
  <h2>New Engagement</h2>
  <form id="eng-form">
    <label>Tenant ID <input id="tenantId" placeholder="t_demo" value="t_demo"></label>
    <label>Name <input id="engName" placeholder="web-scan"></label>
    <label>Type
      <select id="engType">
        <option value="web">web</option>
        <option value="network">network</option>
        <option value="mobile">mobile</option>
      </select>
    </label>
    <label>In-scope domains (comma-separated) <input id="domains" placeholder="example.com"></label>
    <label>In-scope CIDRs (comma-separated) <input id="cidrs" placeholder=""></label>
    <button type="button" onclick="createEngagement()">Create Engagement</button>
  </form>
  <hr>
  <div id="plan-area" class="hidden">
    <h3>Plan</h3>
    <div>
      <button type="button" onclick="autoPlan()">Auto Plan</button>
      <button type="button" onclick="validatePlan()">Validate</button>
      <button type="button" onclick="createPlan()">Create Plan</button>
      <button type="button" onclick="startRun()">Start Run</button>
    </div>
    <div>
      <label>Risk Tier
        <select id="riskTier">
          <option value="safe_passive">safe_passive</option>
          <option value="safe_active" selected>safe_active</option>
          <option value="intrusive">intrusive</option>
        </select>
      </label>
    </div>
    <div id="tests"></div>
    <pre id="validateOut"></pre>
  </div>
</section>
{% endblock %}
```

