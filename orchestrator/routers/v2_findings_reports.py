import os, uuid, json, datetime, hashlib
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, UploadFile, File, Form, Header, Response, Query, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..auth import Principal
from ..tenancy import set_tenant_guc, require_tenant

def month_key(dt=None):
    dt = dt or datetime.datetime.utcnow()
    return dt.strftime("%Y-%m")

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def insert_run_event(db: Session, tenant_id: str, run_id: str, ev_type: str, payload: Dict[str, Any]):
    set_tenant_guc(db, tenant_id)
    db.execute(text("INSERT INTO run_events (id, tenant_id, run_id, type, payload) VALUES (:id,:t,:r,:ty,:pl)"),
               {"id": f"ev_{uuid.uuid4().hex[:12]}", "t": tenant_id, "r": run_id, "ty": ev_type, "pl": json.dumps(payload)})
    db.commit()


router = APIRouter()
EVIDENCE_DIR = os.environ.get("EVIDENCE_DIR","/data/evidence")

@router.post("/v2/runs/{run_id}/findings")
def findings_upsert(run_id: str, body: List[Dict[str, Any]], db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    run = db.execute(text("SELECT tenant_id FROM runs WHERE id=:id"), {"id": run_id}).mappings().first()
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, run["tenant_id"])
    for f in body or []:
        db.execute(text("""
            INSERT INTO findings (id, tenant_id, run_id, title, severity, description, assets, recommendation, tags)
            VALUES (:id,:t,:r,:ti,:se,:de,:as,:re,:ta)
        """), {
            "id": f"vuln_{uuid.uuid4().hex[:10]}", "t": run["tenant_id"], "r": run_id,
            "ti": f.get("title","Untitled"), "se": f.get("severity","info"), "de": f.get("description",""),
            "as": json.dumps(f.get("assets",{})), "re": f.get("recommendation"), "ta": json.dumps(f.get("tags",{}))
        })
    db.commit()
    return {"ok": True}

@router.get("/v2/runs/{run_id}/findings")
def findings_list(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    run = db.execute(text("SELECT tenant_id FROM runs WHERE id=:id"), {"id": run_id}).mappings().first()
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, run["tenant_id"])
    rows = db.execute(text("""
        SELECT id, title, severity, description, assets, recommendation, tags, created_at
        FROM findings WHERE run_id=:r ORDER BY created_at DESC
    """), {"r": run_id}).mappings().all()
    return {"findings": [dict(x) for x in rows]}

@router.post("/v2/runs/{run_id}/artifacts")
async def artifacts_upload(run_id: str, file: UploadFile = File(...), label: str = Form("evidence"), kind: str = Form("generic"),
                           db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    run = db.execute(text("SELECT tenant_id FROM runs WHERE id=:id"), {"id": run_id}).mappings().first()
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, run["tenant_id"])
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    fname = f"{run_id}_{uuid.uuid4().hex[:8]}_{file.filename}"
    path = os.path.join(EVIDENCE_DIR, fname)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    db.execute(text("""
        INSERT INTO artifacts (id, tenant_id, run_id, kind, label, path)
        VALUES (:id,:t,:r,:k,:l,:p)
    """), {"id": f"art_{uuid.uuid4().hex[:10]}", "t": run["tenant_id"], "r": run_id, "k": kind, "l": label, "p": path})
    db.commit()
    return {"ok": True, "path": path}

def _report_data(db: Session, run_id: str) -> Dict[str, Any]:
    r = db.execute(text("SELECT tenant_id, plan_id, engagement_id FROM runs WHERE id=:id"), {"id": run_id}).mappings().first()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r["tenant_id"])
    eng = db.execute(text("SELECT name, type, scope FROM engagements WHERE id=:id"), {"id": r["engagement_id"]}).mappings().first()
    plan = db.execute(text("SELECT data FROM plans WHERE id=:id"), {"id": r["plan_id"]}).mappings().first()
    fnds = db.execute(text("SELECT id, title, severity, description, assets, recommendation, tags FROM findings WHERE run_id=:r"), {"r": run_id}).mappings().all()
    return {"run_id": run_id, "engagement": dict(eng) if eng else {}, "plan": (plan or {}).get("data", {}), "findings": [dict(x) for x in fnds]}

@router.get("/v2/reports/run/{run_id}.json")
def report_json(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    return _report_data(db, run_id)

@router.get("/v2/reports/run/{run_id}.md")
def report_md(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    d = _report_data(db, run_id)
    lines = [f"# Engagement Report — Run {d['run_id']}", "", f"**Engagement**: {d['engagement'].get('name','')} ({d['engagement'].get('type','')})", "", "## Plan Steps"]
    for s in (d.get("plan",{}).get("steps",[]) or []):
        lines.append(f"- {s.get('id')} {'params='+json.dumps(s.get('params')) if s.get('params') else ''}")
    lines.append("\n## Findings")
    if d["findings"]:
        for f in d["findings"]:
            lines += [f"\n### {f['title']} — {f['severity'].upper()}", f.get("description",""), f"**Assets**: `{json.dumps(f.get('assets',{}))}`", f"**Recommendation**: {f.get('recommendation') or '—'}", f"**Tags**: `{json.dumps(f.get('tags',{}))}`"]
    else:
        lines.append("_No findings recorded._")
    return Response("\n".join(lines), media_type="text/markdown")

@router.get("/v2/reports/run/{run_id}.html")
def report_html(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    d = _report_data(db, run_id)
    def esc(s): 
        return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    parts = [f"<h1>Engagement Report — Run {esc(d['run_id'])}</h1>",
             f"<p><strong>Engagement:</strong> {esc(d['engagement'].get('name',''))} ({esc(d['engagement'].get('type',''))})</p>",
             "<h2>Plan Steps</h2><ul>"]
    for s in (d.get("plan",{}).get("steps",[]) or []):
        pr = json.dumps(s.get("params")) if s.get("params") else ""
        parts.append(f"<li>{esc(s.get('id'))} {('<code>params='+esc(pr)+'</code>') if pr else ''}</li>")
    parts.append("</ul><h2>Findings</h2>")
    if d["findings"]:
        for f in d["findings"]:
            parts.append(f"<h3>{esc(f['title'])} — {esc(f['severity']).upper()}</h3><p>{esc(f.get('description',''))}</p>")
            parts.append(f"<p><strong>Assets:</strong> <code>{esc(json.dumps(f.get('assets',{})))}</code></p>")
            parts.append(f"<p><strong>Recommendation:</strong> {esc(f.get('recommendation') or '—')}</p>")
            parts.append(f"<p><strong>Tags:</strong> <code>{esc(json.dumps(f.get('tags',{})))}</code></p>")
    else:
        parts.append("<p><em>No findings recorded.</em></p>")
    html = "<!doctype html><html><head><meta charset='utf-8'><title>Run Report</title></head><body>" + "".join(parts) + "</body></html>"
    return Response(html, media_type="text/html")
