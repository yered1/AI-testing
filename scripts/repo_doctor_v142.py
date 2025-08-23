#!/usr/bin/env python3
import os, sys, json, re

ROOT = os.getcwd()
patterns_junk = [
    r".*/__pycache__/.*",
    r".*\.pyc$", r".*\.pyo$", r".*\.pyd$",
    r".*/\.pytest_cache/.*", r".*/\.mypy_cache/.*",
    r".*/\.tox/.*", r".*/\.coverage.*", r".*/htmlcov/.*",
    r".*/\.DS_Store$", r".*/__MACOSX/.*", r".*/Thumbs\.db$",
    r".*/\.idea/.*", r".*/\.vscode/.*"
]
maybe_big = []
junk = []
for d,_,files in os.walk(ROOT):
    for f in files:
        p = os.path.join(d,f)
        rel = os.path.relpath(p, ROOT)
        try:
            sz = os.path.getsize(p)
            if sz > 10*1024*1024:
                maybe_big.append({"path": rel, "size": sz})
        except Exception:
            pass
        for pat in patterns_junk:
            if re.match(pat, rel):
                junk.append(rel); break

report = {
    "junk_candidates": sorted(junk),
    "large_files_over_10mb": sorted(maybe_big, key=lambda x: -x["size"])[:200]
}
print(json.dumps(report, indent=2))
