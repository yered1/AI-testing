# File: AI-testing/orchestrator/templates/report_run.html.j2

- Size: 877 bytes
- Kind: text
- SHA256: 2424cc78b5d9169c784ee21d8c00e22925bc2573f352199d3751fe1614966312

## Head (first 60 lines)

```
<!doctype html>
<html><head><meta charset="utf-8"><title>Run {{ run_id }} Report</title></head>
<body style="font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;">
<h1>Engagement Report — Run {{ run_id }}</h1>
<p><strong>Engagement:</strong> {{ engagement.name }} ({{ engagement.type }})</p>

<h2>Plan Steps</h2>
<ul>
{% for s in plan.steps %}<li>{{ s.id }} {% if s.params %}<code>params={{ s.params }}</code>{% endif %}</li>{% endfor %}
</ul>

<h2>Findings</h2>
{% if findings %}
{% for f in findings %}
<h3>{{ f.title }} — {{ f.severity|upper }}</h3>
<p>{{ f.description }}</p>
<p><strong>Assets:</strong> <code>{{ f.assets }}</code></p>
<p><strong>Recommendation:</strong> {{ f.recommendation or '—' }}</p>
<p><strong>Tags:</strong> <code>{{ f.tags }}</code></p>
{% endfor %}
{% else %}
<p><em>No findings recorded.</em></p>
{% endif %}
</body></html>
```

