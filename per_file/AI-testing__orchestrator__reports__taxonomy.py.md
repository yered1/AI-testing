# File: AI-testing/orchestrator/reports/taxonomy.py

- Size: 4682 bytes
- Kind: text
- SHA256: fdc22918f503e6ad24c3f83ca8756f9bb7c76b48ae196ea976eefb5d241cc7fd

## Python Imports

```
json
```

## Head (first 60 lines)

```
OWASP_2021 = {
  "A01:2021": "Broken Access Control",
  "A02:2021": "Cryptographic Failures",
  "A03:2021": "Injection",
  "A04:2021": "Insecure Design",
  "A05:2021": "Security Misconfiguration",
  "A06:2021": "Vulnerable and Outdated Components",
  "A07:2021": "Identification and Authentication Failures",
  "A08:2021": "Software and Data Integrity Failures",
  "A09:2021": "Security Logging and Monitoring Failures",
  "A10:2021": "Server-Side Request Forgery (SSRF)"
}

# Minimal keyword heuristics to tag findings when tags not provided
HEURISTICS = [
  ("xss", {"owasp": "A03:2021", "cwe": ["79"], "topic": "Cross-Site Scripting"}),
  ("sql injection", {"owasp": "A03:2021", "cwe": ["89"], "topic": "SQL Injection"}),
  ("open redirect", {"owasp": "A01:2021", "cwe": ["601"], "topic": "Open Redirect"}),
  ("ssrf", {"owasp": "A10:2021", "cwe": ["918"], "topic": "SSRF"}),
  ("csrf", {"owasp": "A01:2021", "cwe": ["352"], "topic": "CSRF"}),
  ("clickjack", {"owasp": "A05:2021", "cwe": ["1021"], "topic": "Clickjacking"}),
]

SEVERITY_ORDER = ["info","low","medium","high","critical"]

def enrich_finding(f):
    tags = f.get("tags") or {}
    title = (f.get("title") or "").lower()
    desc = (f.get("description") or "").lower()
    text = f"{title} {desc}"
    # Copy
    out = dict(f)
    # normalize tags to dict
    if not isinstance(tags, dict):
        try:
            # sometimes tags might be a list or stringified
            import json as _json
            if isinstance(tags, str):
                tags = _json.loads(tags)
            elif isinstance(tags, list):
                tags = {"labels": tags}
            else:
                tags = {}
        except Exception:
            tags = {}
    # If cwe/owasp missing, try heuristics
    if not tags.get("cwe") and not tags.get("cwe_ids"):
        for key, add in HEURISTICS:
            if key in text:
                tags.setdefault("cwe", add.get("cwe"))
                tags.setdefault("topic", add.get("topic"))
                if not tags.get("owasp"): tags["owasp"] = add.get("owasp")
                break
    if not tags.get("owasp"):
        for key, add in HEURISTICS:
            if key in text:
                tags["owasp"] = add.get("owasp")
                break
    out["tags"] = tags
    return out
```

## Tail (last 60 lines)

```
    name = name.upper(); val = val.upper()
    if name == "AV":
        return {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}.get(val)
    if name == "AC":
        return {"L": 0.77, "H": 0.44}.get(val)
    if name == "PR":
        # Depends on scope
        if scope == "U":
            return {"N": 0.85, "L": 0.62, "H": 0.27}.get(val)
        else: # scope changed
            return {"N": 0.85, "L": 0.68, "H": 0.5}.get(val)
    if name == "UI":
        return {"N": 0.85, "R": 0.62}.get(val)
    if name == "S":
        return {"U": "U", "C": "C"}.get(val)
    if name == "C":
        return {"H": 0.56, "L": 0.22, "N": 0.0}.get(val)
    if name == "I":
        return {"H": 0.56, "L": 0.22, "N": 0.0}.get(val)
    if name == "A":
        return {"H": 0.56, "L": 0.22, "N": 0.0}.get(val)
    return None

def cvss_base_score(vector):
    # Example: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
    try:
        parts = vector.strip().split('/')
        if parts[0].startswith("CVSS:"):
            parts = parts[1:]
        metrics = {}
        for p in parts:
            if ':' not in p: continue
            k, v = p.split(':', 1)
            metrics[k] = v
        S = metrics.get("S","U").upper()
        AV = _metric_value("AV", metrics.get("AV"), S)
        AC = _metric_value("AC", metrics.get("AC"), S)
        PR = _metric_value("PR", metrics.get("PR"), S)
        UI = _metric_value("UI", metrics.get("UI"), S)
        C = _metric_value("C", metrics.get("C"), S)
        I = _metric_value("I", metrics.get("I"), S)
        A = _metric_value("A", metrics.get("A"), S)
        if None in (AV,AC,PR,UI,C,I,A): return None
        impact = 1 - ((1 - C) * (1 - I) * (1 - A))
        if S == "U":
            impact_sub = 6.42 * impact
        else:
            impact_sub = 7.52 * (impact - 0.029) - 3.25 * (impact - 0.02) ** 15
        exploitab = 8.22 * AV * AC * PR * UI
        if impact_sub <= 0:
            base = 0.0
        else:
            if S == "U":
                base = min(impact_sub + exploitab, 10)
            else:
                base = min(1.08 * (impact_sub + exploitab), 10)
        # round up to one decimal
        return round((int(base * 10 + 0.000001) + (0 if base*10 == int(base*10) else 1)) / 10.0, 1)
    except Exception:
        return None
```

