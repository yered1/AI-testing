#!/usr/bin/env python3
import os, re, sys, json, hashlib, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

def list_files():
    out=[]
    for dp, dn, fn in os.walk(ROOT):
        for f in fn:
            p = pathlib.Path(dp)/f
            rel = p.relative_to(ROOT)
            out.append((str(rel), p.stat().st_size))
    return out

JUNK_PATTERNS=[
    r'^__MACOSX/',
    r'\.DS_Store$',
    r'\.AppleDouble/',
    r'\.pytest_cache/',
    r'\.mypy_cache/',
    r'/__pycache__/',
    r'\.pyc$',
    r'\.swp$',
    r'~$',
]

def is_junk(rel):
    s=str(rel)
    for pat in JUNK_PATTERNS:
        if re.search(pat,s):
            return True
    return False

def find_bootstrap():
    p = ROOT / "orchestrator" / "bootstrap_extras.py"
    return p if p.exists() else None

def parse_includes(text):
    found = set()
    for m in re.finditer(r'include_router\(\s*([a-zA-Z0-9_\.]+)\.router', text):
        found.add(m.group(1).split('.')[-1])
    return found

def list_routers():
    base = ROOT / "orchestrator" / "routers"
    routers = []
    if not base.exists():
        return routers
    for p in base.glob("*.py"):
        if p.name=="__init__.py": 
            continue
        routers.append(p.stem)
    return sorted(routers)

def main():
    files = list_files()
    junk = [f for f,_ in files if is_junk(f)]
    bs = find_bootstrap()
    includes = set()
    if bs:
        includes = parse_includes(bs.read_text(encoding="utf-8", errors="ignore"))
    routers = list_routers()
    missing = [r for r in routers if r not in includes]
    report = {
        "root": str(ROOT),
        "counts": {
            "files": len(files),
            "junk_candidates": len(junk),
            "routers": len(routers),
            "includes_found": len(includes),
            "missing_includes": len(missing),
        },
        "missing_includes": missing,
        "junk_candidates": junk[:500],
    }
    print(json.dumps(report, indent=2))

if __name__=="__main__":
    main()
