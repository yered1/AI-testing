import hashlib, json, uuid, pathlib, glob, datetime, os, asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, text
import httpx, requests
from sse_starlette.sse import EventSourceResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .db import get_db, SessionLocal
from .models import Engagement, Plan, Run
from .auth import get_principal, Principal
from .tenancy import set_tenant_guc, require_tenant, ensure_membership

APP_ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_DIR = APP_ROOT / "catalog" / "tests"
TEMPLATE_DIR = pathlib.Path(__file__).resolve().parent / "templates"
OPA_URL = os.environ.get("OPA_URL","http://localhost:8181/v1/data/pentest/policy")
SIMULATE = os.environ.get("SIMULATE_PROGRESS","false").lower() == "true"
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")
EVIDENCE_DIR = os.environ.get("EVIDENCE_DIR", "/data/evidence")

env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(enabled_extensions=("html",))
)

app = FastAPI(title="AI Testing Orchestrator (v2)", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FindingIn(BaseModel):
    id: Optional[str] = None
    title: str
    severity: str = Field(pattern="^(info|low|medium|high|critical)$")
    description: Optional[str] = None
    assets: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None  # {"cwe":[...], "owasp":[...]}
    cvss_vector: Optional[str] = None
    cvss_score: Optional[float] = None
    recommendation: Optional[str] = None
    status: str = Field(default="open")

class FindingOut(FindingIn):
    id: str

def ensure_dir(p: pathlib.Path):
    p.mkdir(parents=True, exist_ok=True)

def safe_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-","_",".")).strip()[:200] or f"file_{uuid.uuid4().hex[:8]}"

@app.post("/v2/runs/{run_id}/findings")
def findings_upsert(run_id: str, body: List[FindingIn], db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(select(Run).where(Run.id == run_id)).scalar_one_or_none()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r.tenant_id)
    out = []
    for f in body:
        fid = f.id or f"find_{uuid.uuid4().hex[:10]}"
        db.execute(text('''
            INSERT INTO findings (id, tenant_id, run_id, engagement_id, title, severity, description, assets, tags, cvss_vector, cvss_score, recommendation, status)
            VALUES (:id,:t,:r,:e,:title,:sev,:desc,:assets,:tags,:cvss_vec,:cvss_score,:rec,:status)
            ON CONFLICT (id) DO UPDATE SET
                title=EXCLUDED.title, severity=EXCLUDED.severity, description=EXCLUDED.description,
                assets=EXCLUDED.assets, tags=EXCLUDED.tags, cvss_vector=EXCLUDED.cvss_vector,
                cvss_score=EXCLUDED.cvss_score, recommendation=EXCLUDED.recommendation, status=EXCLUDED.status,
                updated_at=now()
        '''), {
            "id": fid, "t": r.tenant_id, "r": r.id, "e": r.engagement_id,
            "title": f.title, "sev": f.severity, "desc": f.description,
            "assets": json.dumps(f.assets) if f.assets is not None else None,
            "tags": json.dumps(f.tags) if f.tags is not None else None,
            "cvss_vec": f.cvss_vector, "cvss_score": f.cvss_score, "rec": f.recommendation, "status": f.status
        })
        out.append({"id": fid})
    db.commit()
    return {"ok": True, "findings": out}

@app.get("/v2/runs/{run_id}/findings")
def findings_list(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(select(Run).where(Run.id == run_id)).scalar_one_or_none()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r.tenant_id)
    rows = db.execute(text('''
        SELECT id,title,severity,description,assets,tags,cvss_vector,cvss_score,recommendation,status
        FROM findings WHERE run_id=:r ORDER BY
          CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 ELSE 5 END, created_at ASC
    '''), {"r": run_id}).mappings().all()
    res = []
    for row in rows:
        res.append({
            **{k: row[k] for k in ["id","title","severity","description","cvss_vector","cvss_score","recommendation","status"]},
            "assets": row["assets"],
            "tags": row["tags"],
        })
    return {"findings": res}

@app.post("/v2/runs/{run_id}/artifacts")
async def artifact_upload(run_id: str, finding_id: Optional[str] = Form(default=None), file: UploadFile = File(...),
                          db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(select(Run).where(Run.id == run_id)).scalar_one_or_none()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r.tenant_id)

    base = pathlib.Path(EVIDENCE_DIR) / r.tenant_id / "runs" / run_id
    ensure_dir(base)
    fname = safe_filename(file.filename or f"file_{uuid.uuid4().hex[:8]}")
    fpath = base / fname
    content = await file.read()
    with open(fpath, "wb") as f:
        f.write(content)
    size = len(content)
    ctype = file.content_type

    db.execute(text('''
        INSERT INTO artifacts (id, tenant_id, run_id, finding_id, kind, path, filename, content_type, size)
        VALUES (:id,:t,:r,:f,'file',:p,:n,:ct,:sz)
    '''), {"id": f"art_{uuid.uuid4().hex[:10]}", "t": r.tenant_id, "r": run_id, "f": finding_id,
           "p": str(fpath), "n": fname, "ct": ctype, "sz": size})
    db.commit()
    return {"ok": True, "filename": fname, "size": size, "content_type": ctype, "path": str(fpath)}

def _collect_report(db: Session, run_id: str) -> dict:
    r = db.execute(select(Run).where(Run.id == run_id)).scalar_one_or_none()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r.tenant_id)

    eng = db.execute(text('SELECT id,name,type,scope FROM engagements WHERE id=:e'), {"e": r.engagement_id}).mappings().first()
    findings = db.execute(text('''
        SELECT id,title,severity,description,assets,tags,cvss_vector,cvss_score,recommendation,status
        FROM findings WHERE run_id=:r ORDER BY
          CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 ELSE 5 END, created_at ASC
    '''), {"r": run_id}).mappings().all()

    by_finding = {}
    art_rows = db.execute(text('SELECT finding_id, filename, content_type, size, path FROM artifacts WHERE run_id=:r'),
                          {"r": run_id}).mappings().all()
    for a in art_rows:
        fid = a["finding_id"]
        if fid:
            by_finding.setdefault(fid, []).append(dict(a))
    findings_enriched = []
    for f in findings:
        d = dict(f)
        d["artifacts"] = by_finding.get(f["id"], [])
        findings_enriched.append(d)

    return {
        "run_id": run_id,
        "tenant_id": r.tenant_id,
        "engagement_id": r.engagement_id,
        "engagement": eng,
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "findings": findings_enriched
    }

@app.get("/v2/reports/run/{run_id}.json")
def report_json(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    data = _collect_report(db, run_id)
    return data

@app.get("/v2/reports/run/{run_id}.md")
def report_md(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    data = _collect_report(db, run_id)
    tmpl = env.get_template("report_run.md.j2")
    md = tmpl.render(**data)
    return Response(content=md, media_type="text/markdown")

@app.get("/v2/reports/run/{run_id}.html")
def report_html(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    data = _collect_report(db, run_id)
    tmpl = env.get_template("report_run.html.j2")
    html = tmpl.render(**data)
    return Response(content=html, media_type="text/html")
