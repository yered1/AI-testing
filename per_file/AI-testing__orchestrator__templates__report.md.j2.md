# File: AI-testing/orchestrator/templates/report.md.j2

- Size: 1291 bytes
- Kind: text
- SHA256: 118fd350cd98c27dc94ec0d9b911526d8800190d7d6d3ed4d91fd8f98c91984e

## Head (first 60 lines)

```
# Pentest Report — {{ engagement.name }}
_Tenant_: {{ tenant_id }}  
_Generated_: {{ generated_at }}

## Scope
{% if engagement.scope.in_scope_domains %}
**Domains**: {{ engagement.scope.in_scope_domains | join(", ") }}
{% endif %}
{% if engagement.scope.in_scope_cidrs %}
**CIDRs**: {{ engagement.scope.in_scope_cidrs | join(", ") }}
{% endif %}
{% if engagement.scope.out_of_scope %}
**Out of scope**: {{ engagement.scope.out_of_scope | join(", ") }}
{% endif %}

## Summary
Total findings: **{{ findings|length }}**  
Critical: **{{ counts.critical }}**, High: **{{ counts.high }}**, Medium: **{{ counts.medium }}**, Low: **{{ counts.low }}**, Info: **{{ counts.info }}**

## Findings
{% for f in findings %}
### {{ loop.index }}. {{ f.title }} ({{ f.severity|upper }})
- **Status**: {{ f.status }}
- **Category**: {{ f.category or "-" }}
- **CWE**: {{ f.cwe or "-" }} | **OWASP**: {{ f.owasp or "-" }} | **CVSS**: {{ f.cvss or "-" }}
- **Affected**: {% if f.affected_assets %}{{ f.affected_assets | tojson }}{% else %}-{% endif %}

**Description**  
{{ f.description or "-" }}

**Recommendation**  
{{ f.recommendation or "-" }}

{% if f.evidence and f.evidence|length > 0 %}
**Evidence**  
{% for e in f.evidence %}- ({{ e.type }}) {{ e.value }}
{% endfor %}
{% endif %}
{% endfor %}
```

