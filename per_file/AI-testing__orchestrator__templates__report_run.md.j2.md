# File: AI-testing/orchestrator/templates/report_run.md.j2

- Size: 509 bytes
- Kind: text
- SHA256: 31354ffefa8d080a4a498ae1885501f28c853a6e2d00787cada9ba4051cc1dc5

## Head (first 60 lines)

```
# Engagement Report — Run {{ run_id }}

**Engagement**: {{ engagement.name }} ({{ engagement.type }})

## Plan Steps
{% for s in plan.steps %}
- {{ s.id }} {% if s.params %}params={{ s.params }}{% endif %}
{% endfor %}

## Findings
{% if findings %}
{% for f in findings %}
### {{ f.title }} — {{ f.severity|upper }}
{{ f.description }}

**Assets**: `{{ f.assets }}`
**Recommendation**: {{ f.recommendation or '—' }}
**Tags**: `{{ f.tags }}`

{% endfor %}
{% else %}
_No findings recorded._
{% endif %}
```

