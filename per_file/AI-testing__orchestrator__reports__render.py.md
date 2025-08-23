# File: AI-testing/orchestrator/reports/render.py

- Size: 2302 bytes
- Kind: text
- SHA256: 7c027b14935cab75a3245baa145302b487aa45b8fd72a8075096bd2cc11859bd

## Python Imports

```
datetime, jinja2, json, os, requests, taxonomy
```

## Head (first 60 lines)

```
import os, json, datetime, requests
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .taxonomy import OWASP_2021, SEVERITY_ORDER, enrich_finding, cvss_base_score

def _env(template_dir):
    return Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html', 'xml'])
    )

def _sev_badge(sev):
    sev = (sev or 'info').lower()
    color = {'critical':'#8b0000','high':'#b22222','medium':'#ff8c00','low':'#2e8b57','info':'#4682b4'}.get(sev,'#4682b4')
    return f"<span style='background:{color};color:white;padding:2px 6px;border-radius:4px;font-size:12px'>{sev.upper()}</span>"

def _enrich_findings(findings):
    out = []
    for f in findings:
        ef = enrich_finding(f)
        tags = ef.get("tags") or {}
        vec = tags.get("cvss_vector") or tags.get("cvss") or tags.get("cvss:vector")
        if vec and not tags.get("cvss_score"):
            score = cvss_base_score(vec)
            if score is not None:
                tags["cvss_score"] = score
        ef["tags"] = tags
        out.append(ef)
    return out

def build_context(data: dict) -> dict:
    # data keys: run_id, engagement{name,type,scope}, plan{steps}, findings[]
    d = dict(data) if data else {}
    d["generated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    d["owasp"] = OWASP_2021
    d["findings"] = _enrich_findings(d.get("findings") or [])
    # severity sort
    d["findings_sorted"] = sorted(d["findings"], key=lambda f: SEVERITY_ORDER.index((f.get('severity') or 'info').lower()) if (f.get('severity') or 'info').lower() in SEVERITY_ORDER else 0, reverse=True)
    # artifacts summary (if present in data)
    return d

def render_html(template_dir: str, data: dict) -> str:
    env = _env(template_dir)
    tmpl = env.get_template("enhanced.html")
    ctx = build_context(data)
    return tmpl.render(**ctx)

def render_md(template_dir: str, data: dict) -> str:
    env = _env(template_dir)
    tmpl = env.get_template("enhanced.md.j2")
    ctx = build_context(data)
    return tmpl.render(**ctx)

def render_pdf(reporter_url: str, html: str, title: str = "Report"):
    r = requests.post(reporter_url.rstrip('/') + "/render/pdf", json={"html": html, "title": title}, timeout=60)
    r.raise_for_status()
    return r.content
```

