#!/usr/bin/env python3
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
bootstrap = ROOT / "orchestrator" / "bootstrap_extras.py"
routers_dir = ROOT / "orchestrator" / "routers"

if not bootstrap.exists():
    print("bootstrap_extras.py not found", file=sys.stderr); sys.exit(1)

code = bootstrap.read_text(encoding="utf-8", errors="ignore")
present = set(re.findall(r'from \.routers import ([^\n]+)', code))
imports = set()
for m in present:
    for part in m.split(","):
        imports.add(part.strip())

include_present = set()
for m in re.finditer(r'include_router\(\s*([a-zA-Z0-9_\.]+)\.router', code):
    include_present.add(m.group(1).split(".")[-1])

# list routers
routers = [p.stem for p in routers_dir.glob("*.py") if p.name!="__init__.py"]
missing = [r for r in routers if r not in include_present]

if not missing:
    print("No missing routers. Nothing to do.")
    sys.exit(0)

# Build import line
to_add = ", ".join(sorted(missing))
ins_import = f"from .routers import {to_add}\n"
# Build include lines
ins_includes = "".join([f"app.include_router({r}.router)\n" for r in sorted(missing)])

# Insert imports after initial imports from .routers if present; else add after first line
lines = code.splitlines(True)
insert_at = None
for i,l in enumerate(lines):
    if l.startswith("from .routers import"):
        insert_at = i+1
last_from_init = None
if insert_at is None:
    for i,l in enumerate(lines):
        if l.startswith("from .app_v2 import app"):
            insert_at = i+1
            break

if insert_at is None:
    insert_at = 0

lines.insert(insert_at, ins_import)
# Append includes at end
lines.append("\n# auto-added by fix_bootstrap_includes_v141.py\n")
lines.append(ins_includes)

bootstrap.write_text("".join(lines), encoding="utf-8")
print(f"Added routers: {', '.join(missing)}")
