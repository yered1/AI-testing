#!/usr/bin/env python3
import os, json, re, pathlib

root = pathlib.Path(__file__).resolve().parents[1]
routers = sorted((root/"orchestrator"/"routers").glob("*.py"))
be = root/"orchestrator"/"bootstrap_extras.py"
missing = []

if be.exists():
    txt = be.read_text(encoding="utf-8", errors="ignore")
    for r in routers:
        if r.name == "__init__.py": continue
        mod = r.stem
        if mod not in txt:
            missing.append(mod)
else:
    missing = [r.stem for r in routers if r.name != "__init__.py"]

report = {
 "bootstrap_extras": str(be),
 "routers_total": len(routers),
 "missing_includes": missing,
}
print(json.dumps(report, indent=2))
