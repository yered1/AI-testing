# File: AI-testing/orchestrator/report_templates/enhanced.md.j2

- Size: 1374 bytes
- Kind: text
- SHA256: df078a691ef8cac18e8d49c9c50057765ba49b88fe6c5217fe2c6aa4dd91bc6f

## Head (first 60 lines)

```
# Engagement Report — Run {{ run_id }}

**Generated:** {{ generated_at }}  
**Engagement:** {{ engagement.get('name','') }} ({{ engagement.get('type','') }})

## Plan
{% if plan and plan.get('steps') -%}
| Step | Parameters |
|------|------------|
{% for s in plan.get('steps') -%}
| `{{ s.get('id') }}` | `{{ (s.get('params') or {}) | tojson }}` |
{% endfor -%}
{% else -%}
_No plan steps recorded._
{% endif -%}

## Findings
{% if findings_sorted -%}
| Title | Severity | Taxonomy | Description | Recommendation |
|-------|----------|----------|-------------|----------------|
{% for f in findings_sorted -%}
{% set t = f.get('tags') or {} -%}
| **{{ f.get('title','') }}** | {{ f.get('severity','').upper() }} | {% if t.get('cwe') %}CWE {{ t.get('cwe') }}{% endif %}{% if t.get('owasp') %} {% if t.get('cwe') %}<br/>{% endif %}OWASP {{ t.get('owasp') }}{% endif %}{% if t.get('cvss_score') %} {% if t.get('owasp') or t.get('cwe') %}<br/>{% endif %}CVSS {{ t.get('cvss_score') }}{% endif %} | {{ f.get('description','') }} | {{ f.get('recommendation') or '—' }} |
{% endfor -%}
{% else -%}
_No findings recorded._
{% endif -%}

## Artifacts
{% if artifacts -%}
| Label | Kind | Path |
|-------|------|------|
{% for a in artifacts -%}
| {{ a.get('label') }} | {{ a.get('kind') }} | `{{ a.get('path') }}` |
{% endfor -%}
{% else -%}
_No artifacts listed._
{% endif -%}
```

