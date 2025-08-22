import os, io, json, tempfile, zipfile, datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..db import get_db
from ..auth import Principal
from ..tenancy import set_tenant_guc, require_tenant

router = APIRouter()

def _report_data(db: Session, run_id: str) -> Dict[str, Any]:
    r = db.execute(text("SELECT tenant_id, plan_id, engagement_id FROM runs WHERE id=:id"),
                   {"id": run_id}).mappings().first()
    if not r:
        raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r["tenant_id"])
    eng = db.execute(text("SELECT name, type, scope FROM engagements WHERE id=:id"),
                     {"id": r["engagement_id"]}).mappings().first()
    plan = db.execute(text("SELECT data FROM plans WHERE id=:id"),
                      {"id": r["plan_id"]}).mappings().first()
    fnds = db.execute(text("SELECT id, title, severity, description, assets, recommendation, tags FROM findings WHERE run_id=:r"),
                      {"r": run_id}).mappings().all()
    arts = db.execute(text("SELECT id, kind, label, path, created_at FROM artifacts WHERE run_id=:r ORDER BY created_at ASC"),
                      {"r": run_id}).mappings().all()
    return {
        "run_id": run_id,
        "tenant_id": r["tenant_id"],
        "engagement": dict(eng) if eng else {},
        "plan": (plan or {}).get("data", {}),
        "findings": [dict(x) for x in fnds],
        "artifacts": [dict(a) for a in arts],
        "generated_at": datetime.datetime.utcnow().isoformat()+"Z"
    }

def _render_md(d: Dict[str, Any]) -> str:
    lines = [f"# Engagement Report — Run {d.get('run_id')}", ""]
    e = d.get("engagement") or {}
    lines += [f"**Engagement**: {e.get('name','')} ({e.get('type','')})", ""]
    lines.append("## Plan Steps")
    for s in (d.get("plan",{}).get("steps",[]) or []):
        pr = s.get("params")
        lines.append(f"- {s.get('id')} " + (f"`params={json.dumps(pr)}`" if pr else ""))
    lines.append("")
    lines.append("## Findings")
    fnds = d.get("findings") or []
    if not fnds:
        lines.append("_No findings recorded._")
    else:
        for f in fnds:
            lines += [f"### {f.get('title','Untitled')} — {str(f.get('severity','')).upper()}",
                      f.get("description","") or "",
                      f"**Assets**: `{json.dumps(f.get('assets',{}))}`",
                      f"**Recommendation**: {f.get('recommendation') or '—'}",
                      f"**Tags**: `{json.dumps(f.get('tags',{}))}`",
                      ""]
    lines.append("## Artifacts")
    arts = d.get("artifacts") or []
    if not arts:
        lines.append("_No artifacts._")
    else:
        for a in arts:
            lines.append(f"- [{a.get('label') or a.get('kind') or a.get('id')}]({os.path.basename(a.get('path') or '')})")
    return "\n".join(lines)

def _render_html(d: Dict[str, Any]) -> str:
    def esc(s): return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    parts = [f"<h1>Engagement Report — Run {esc(d.get('run_id'))}</h1>"]
    e = d.get("engagement") or {}
    parts.append(f"<p><strong>Engagement:</strong> {esc(e.get('name',''))} ({esc(e.get('type',''))})</p>")
    parts.append("<h2>Plan Steps</h2><ul>")
    for s in (d.get("plan",{}).get("steps",[]) or []):
        pr = json.dumps(s.get("params")) if s.get("params") else ""
        parts.append(f"<li>{esc(s.get('id'))} {(f'<code>params={esc(pr)}</code>' if pr else '')}</li>")
    parts.append("</ul><h2>Findings</h2>")
    fnds = d.get("findings") or []
    if not fnds:
        parts.append("<p><em>No findings recorded.</em></p>")
    else:
        for f in fnds:
            parts.append(f"<h3>{esc(f.get('title','Untitled'))} — {esc(str(f.get('severity','')).upper())}</h3>")
            parts.append(f"<p>{esc(f.get('description',''))}</p>")
            parts.append(f"<p><strong>Assets:</strong> <code>{esc(json.dumps(f.get('assets',{})))}</code></p>")
            parts.append(f"<p><strong>Recommendation:</strong> {esc(f.get('recommendation') or '—')}</p>")
            parts.append(f"<p><strong>Tags:</strong> <code>{esc(json.dumps(f.get('tags',{})))}</code></p>")
    parts.append("<h2>Artifacts</h2>")
    arts = d.get("artifacts") or []
    if not arts:
        parts.append("<p><em>No artifacts.</em></p>")
    else:
        parts.append("<ul>")
        for a in arts:
            fname = os.path.basename(a.get("path") or "")
            label = a.get("label") or a.get("kind") or a.get("id")
            parts.append(f"<li><a href='{esc(fname)}'>{esc(label)}</a> <small>({esc(fname)})</small></li>")
        parts.append("</ul>")
    return "<!doctype html><html><head><meta charset='utf-8'><title>Run Report</title></head><body>" + "".join(parts) + "</body></html>"

@router.get("/v2/runs/{run_id}/artifacts/index.json")
def artifacts_index(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    d = _report_data(db, run_id)
    return {"run_id": run_id, "artifacts": d.get("artifacts", [])}

@router.get("/v2/reports/run/{run_id}.zip")
def report_bundle(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    d = _report_data(db, run_id)
    # Build a temp zip
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{run_id}.zip") as tf:
        zip_path = tf.name
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Write reports
            md = _render_md(d).encode("utf-8")
            html = _render_html(d).encode("utf-8")
            j = json.dumps(d, indent=2).encode("utf-8")
            zf.writestr("report.md", md)
            zf.writestr("report.html", html)
            zf.writestr("report.json", j)
            # Add artifacts (if accessible)
            for a in d.get("artifacts", []) or []:
                path = a.get("path")
                if not path: continue
                if not os.path.exists(path): continue
                # Place under artifacts/ with original base filename
                base = os.path.basename(path)
                zf.write(path, f"artifacts/{base}")
        return FileResponse(zip_path, media_type="application/zip",
                            filename=f"run_{run_id}_bundle.zip")
    except Exception as e:
        try:
            os.remove(zip_path)
        except Exception:
            pass
        raise
