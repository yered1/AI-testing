# File: AI-testing/orchestrator/ui/templates/code_review.html

- Size: 1313 bytes
- Kind: text
- SHA256: 92252bf1a0210398bc0b67dde53fc0728aae7471bedcd43d79f21365dae63dde

## Head (first 60 lines)

```
{% extends "base.html" %}
{% block title %}Code Review{% endblock %}
{% block content %}
<h2>Secure Code Review</h2>
<ol>
  <li>Create Code Engagement</li>
  <li>Auto-plan with <code>default_code_review</code></li>
  <li>Create Plan and Start Run</li>
  <li>Upload your code package (.zip/.tar.gz) as <code>code_package</code></li>
  <li>Start Semgrep Agent; watch findings</li>
</ol>

<div class="panel">
  <h3>1) Create Engagement</h3>
  <label>Name <input id="eng_name" value="code-review"></label>
  <button onclick="createEng()">Create</button>
  <pre id="eng_out"></pre>
</div>

<div class="panel">
  <h3>2) Plan with default_code_review</h3>
  <button onclick="autoPlan()">Auto Plan</button>
  <pre id="plan_out"></pre>
</div>

<div class="panel">
  <h3>3) Create Plan & Start Run</h3>
  <button onclick="createPlan()">Create Plan</button>
  <button onclick="startRun()">Start Run</button>
  <pre id="run_out"></pre>
</div>

<div class="panel">
  <h3>4) Upload Code Package</h3>
  <input type="file" id="codefile" />
  <button onclick="uploadCode()">Upload</button>
  <pre id="upload_out"></pre>
</div>

<div class="panel">
  <h3>5) Findings</h3>
  <button onclick="listFindings()">Refresh Findings</button>
  <pre id="findings_out"></pre>
</div>

<script src="/ui/static/code.js"></script>
{% endblock %}
```

