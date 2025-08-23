# File: AI-testing/orchestrator/ui/templates/run_detail.html

- Size: 574 bytes
- Kind: text
- SHA256: 3ac81febd0e0218546840d137b66c5cf95c9ebf2e2545cb6afba1fdb454381b7

## Head (first 60 lines)

```
{% extends "base.html" %}
{% block content %}
<section>
  <h2>Run: {{ run_id }}</h2>
  <div>
    <button onclick="openReport('{{ run_id }}','html')">Open HTML</button>
    <button onclick="openReport('{{ run_id }}','md')">Open MD</button>
    <button onclick="openBundle('{{ run_id }}')">Download ZIP</button>
  </div>
  <h3>Live Events</h3>
  <pre id="events" class="stream"></pre>
  <h3>Artifacts</h3>
  <button onclick="loadArtifacts('{{ run_id }}')">Refresh</button>
  <ul id="artifactList"></ul>
</section>
<script>window.RUN_ID="{{ run_id }}";</script>
{% endblock %}
```

