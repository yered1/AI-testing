#!/usr/bin/env python3

import os, sys, re, json, hashlib, time, argparse, shutil
from pathlib import Path

SAFE_DELETE = [
    "**/__pycache__/**", "**/*.pyc", "**/.pytest_cache/**", "**/.DS_Store",
    "**/*~", "**/.coverage", "**/.mypy_cache/**"
]

def human(n):
    for u in ["B","KB","MB","GB"]:
        if n < 1024: return f"{n:.1f}{u}"
        n/=1024
    return f"{n:.1f}TB"

def find(root, pattern):
    return [str(p) for p in Path(root).rglob(pattern)]

def scan(root):
    stats = {"files":0,"bytes":0,"by_ext":{}}
    for p in Path(root).rglob("*"):
        if p.is_file():
            stats["files"]+=1
            sz = p.stat().st_size
            stats["bytes"]+=sz
            ext = p.suffix.lower() or "<noext>"
            stats["by_ext"][ext]=stats["by_ext"].get(ext,0)+1
    return stats

def grep_file(p, patterns):
    try:
        txt = Path(p).read_text(errors="ignore")
        return {k: (k in txt) for k in patterns}
    except Exception:
        return {k: False for k in patterns}

def audit(root):
    out = {"time": time.time(), "root": root, "issues": [], "summary": {}}
    # bootstrap includes
    be = Path(root)/"orchestrator"/"bootstrap_extras.py"
    if be.exists():
        patterns = [
            "v2_quotas_approvals","v2_findings_reports","v2_agents_bus",
            "v2_reports_bundle","v2_artifacts_downloads",
            "v2_reports_enhanced","v3_brain","v3_brain_guarded",
            "ui_pages","ui_code","ui_mobile","ui_builder","ui_brain"
        ]
        found = grep_file(be, patterns)
        out["bootstrap_includes"]=found
    else:
        out["issues"].append("Missing orchestrator/bootstrap_extras.py")

    # endpoints quick grep
    endpoints = {
        "lease2": "/v2/agents/lease2",
        "artifact_upload": "/v2/jobs/{job_id}/artifacts",
        "bundle_zip": "/v2/reports/run/{run_id}.zip",
        "enhanced_pdf": "/v2/reports/enhanced/run/{run_id}.pdf",
        "brain_guarded": "/v3/brain/plan/guarded"
    }
    ep_hits = {}
    for py in Path(root/"orchestrator").rglob("*.py"):
        try:
            txt = py.read_text(errors="ignore")
            for k,v in endpoints.items():
                ep_hits.setdefault(k, False)
                if v in txt: ep_hits[k]=True
        except Exception:
            pass
    out["endpoints_present"]=ep_hits

    # agent packages
    agents_dir = Path(root)/"agents"
    agents = []
    if agents_dir.exists():
        for p in agents_dir.iterdir():
            if p.is_dir() and (p/"agent.py").exists():
                agents.append(p.name)
    out["agents"]=agents

    # junk report
    junk = []
    for pat in SAFE_DELETE:
        junk += find(root, pat)
    out["junk_candidates"]=junk

    out["summary"]["file_stats"]=scan(root)
    return out

def cleanup(root, apply=False):
    junk = []
    for pat in SAFE_DELETE:
        for p in Path(root).rglob(pat):
            junk.append(p)
    removed = []
    for p in junk:
        try:
            if apply:
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    p.unlink(missing_ok=True)
                removed.append(str(p))
        except Exception:
            pass
    return removed

def main():
    ap = argparse.ArgumentParser(description="Repo Doctor (audit & safe cleanup)")
    ap.add_argument("--apply-safe", action="store_true", help="Delete cache files only (pyc, __pycache__, .pytest_cache, .DS_Store)")
    ap.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    res = audit(root)
    if args.apply_safe:
        removed = cleanup(root, apply=True)
        res["removed"] = removed
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print("== Repo Doctor ==")
        print(f"Root: {res['root']} | files: {res['summary']['file_stats']['files']} | size: {human(res['summary']['file_stats']['bytes'])}")
        print("\n-- Bootstrap includes --")
        for k,v in res.get("bootstrap_includes",{}).items():
            print(f"{k}: {'OK' if v else 'MISSING'}")
        print("\n-- Endpoints --")
        for k,v in res.get("endpoints_present",{}).items():
            print(f"{k}: {'OK' if v else 'MISSING'}")
        print("\n-- Agents --")
        print(", ".join(res.get("agents",[])) or "none")
        print(f"\n-- Junk candidates (safe): {len(res['junk_candidates'])} files/dirs")
        print("Use --apply-safe to remove cache files only.")

if __name__ == "__main__":
    main()
