#!/usr/bin/env python3
import os, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
routers_dir = ROOT / "orchestrator" / "routers"
bootstrap = ROOT / "orchestrator" / "bootstrap_extras.py"

if not routers_dir.exists():
    print(f"Routers directory not found: {routers_dir}", file=sys.stderr)
    sys.exit(1)

router_modules = []
for p in sorted(routers_dir.glob("*.py")):
    if p.name == "__init__.py":
        continue
    mod = p.stem
    router_modules.append(mod)

# Heuristic tags by module name
tag_map = {
    "v2_quotas_approvals": ["quotas","approvals"],
    "v2_findings_reports": ["findings","artifacts","reports"],
    "v2_agents_bus": ["agents"],
    "v2_agents_bus_lease2": ["agents"],
    "v2_agents_artifacts": ["agents","artifacts"],
    "v2_listings": ["listings"],
    "v2_brain": ["brain"],
    "v2_reports_bundle": ["reports"],
    "v2_reports_enhanced": ["reports"],
    "v2_artifacts_downloads": ["artifacts"],
    "v3_brain": ["brain-v3"],
    "v3_brain_guarded": ["brain-v3"],
    "ui_pages": ["ui"],
    "ui_code": ["ui"],
    "ui_mobile": ["ui"],
    "ui_builder": ["ui"],
    "ui_brain": ["ui"]
}

lines = []
lines.append("from .app_v2 import app")
imports = []
includes = []

for mod in router_modules:
    imports.append(f"from .routers import {mod}")
    tags = tag_map.get(mod, ["api"])
    if mod.startswith("ui_"):
        includes.append(f"app.include_router({mod}.router, tags={tags})")
        includes.append("try:\n    {0}.mount_static(app)\nexcept Exception:\n    pass".format(mod))
    else:
        includes.append(f"app.include_router({mod}.router, tags={tags})")

content = "\n".join(lines + imports + [""] + includes) + "\n"

# Write canonical bootstrap_extras.py
bootstrap.write_text(content, encoding="utf-8")
print(f"Wrote canonical {bootstrap}")
