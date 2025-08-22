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

# --- Batch 5 overlay (append to orchestrator/app_v2.py) ---
import base64
from fastapi import Body

ARTIFACT_DIR = os.environ.get("ARTIFACT_DIR","/app/data/artifacts")
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def finding_hash(title: str, category: str | None, assets: dict | None) -> str:
    payload = json.dumps({"t": title, "c": category, "a": assets or {}}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]

def create_artifact(db: Session, tenant_id: str, run_id: str, filename: str, b64: str, mime: str | None, kind="file") -> str:
    set_tenant_guc(db, tenant_id)
    raw = base64.b64decode(b64.encode())
    aid = f"af_{uuid.uuid4().hex[:10]}"
    # Write file
    path = os.path.join(ARTIFACT_DIR, f"{aid}_{filename}")
    with open(path, "wb") as f:
        f.write(raw)
    db.execute(
        text("INSERT INTO artifacts (id, tenant_id, run_id, kind, uri, mime, metadata) VALUES (:id,:t,:r,:k,:u,:m,:md)"),
        {"id": aid, "t": tenant_id, "r": run_id, "k": kind, "u": path, "m": mime, "md": json.dumps({})}
    )
    db.commit()
    return aid, path

class EvidenceItem(BaseModel):
    filename: str
    content_base64: str
    mime: Optional[str] = None

class FindingIn(BaseModel):
    title: str
    severity: str  # info|low|medium|high|critical
    category: Optional[str] = None
    cwe: Optional[str] = None
    owasp: Optional[str] = None
    cvss: Optional[float] = None
    affected_assets: Optional[dict] = None
    description: Optional[str] = None
    recommendation: Optional[str] = None
    evidence: Optional[List[EvidenceItem]] = None

class FindingsIngest(BaseModel):
    findings: List[FindingIn]

@app.post("/v2/runs/{run_id}/findings:ingest")
def ingest_findings(run_id: str, body: FindingsIngest, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(select(Run).where(Run.id == run_id)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r.tenant_id)

    created = []
    for f in body.findings:
        h = finding_hash(f.title, f.category, f.affected_assets)
        fid = f"fd_{uuid.uuid4().hex[:10]}"
        # insert finding
        db.execute(
            text("""
                INSERT INTO findings (
                    id, tenant_id, engagement_id, run_id, hash, title, severity, category, cwe, owasp, cvss,
                    affected_assets, description, recommendation
                ) VALUES (
                    :id, :t, :e, :r, :h, :ti, :sev, :cat, :cwe, :ow, :cvss, :assets, :desc, :rec
                )
            """),
            {
                "id": fid, "t": r.tenant_id, "e": r.engagement_id, "r": r.id, "h": h, "ti": f.title,
                "sev": f.severity, "cat": f.category, "cwe": f.cwe, "ow": f.owasp, "cvss": f.cvss,
                "assets": json.dumps(f.affected_assets), "desc": f.description, "rec": f.recommendation
            }
        )
        # evidence
        if f.evidence:
            for ev in f.evidence:
                aid, path = create_artifact(db, r.tenant_id, r.id, ev.filename, ev.content_base64, ev.mime)
                db.execute(
                    text("INSERT INTO evidence_links (id, tenant_id, finding_id, artifact_id) VALUES (:id,:t,:f,:a)"),
                    {"id": f"el_{uuid.uuid4().hex[:10]}", "t": r.tenant_id, "f": fid, "a": aid}
                )
        db.commit()
        created.append({"id": fid, "hash": h})

    insert_event(db, r.tenant_id, r.id, "findings.ingested", {"count": len(created)})
    return {"ok": True, "created": created}

@app.get("/v2/runs/{run_id}/findings")
def list_run_findings(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(select(Run).where(Run.id == run_id)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r.tenant_id)
    rows = db.execute(
        text("""
            SELECT id, title, severity, category, cwe, owasp, cvss, affected_assets, state, created_at
            FROM findings WHERE run_id=:r ORDER BY severity DESC, created_at DESC
        """),
        {"r": run_id}
    ).mappings().all()
    return {"findings": [dict(x) for x in rows]}

@app.get("/v2/engagements/{engagement_id}/findings")
def list_eng_findings(engagement_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(select(Engagement).where(Engagement.id == engagement_id)).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="engagement not found")
    set_tenant_guc(db, e.tenant_id)
    rows = db.execute(
        text("""
            SELECT id, title, severity, category, cwe, owasp, cvss, affected_assets, state, created_at, run_id
            FROM findings WHERE engagement_id=:e ORDER BY created_at DESC
        """),
        {"e": engagement_id}
    ).mappings().all()
    return {"findings": [dict(x) for x in rows]}

@app.get("/v2/findings/{finding_id}")
def get_finding(finding_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    row = db.execute(
        text("""
            SELECT tenant_id, id, title, severity, category, cwe, owasp, cvss, affected_assets, description, recommendation, state, run_id, engagement_id
            FROM findings WHERE id=:id
        """),
        {"id": finding_id}
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    set_tenant_guc(db, row["tenant_id"])
    art = db.execute(
        text("""
            SELECT a.id, a.kind, a.uri, a.mime FROM artifacts a
            JOIN evidence_links e ON e.artifact_id = a.id
            WHERE e.finding_id=:f
        """),
        {"f": finding_id}
    ).mappings().all()
    data = dict(row)
    data["artifacts"] = [dict(x) for x in art]
    return data

class FindingStateIn(BaseModel):
    state: str  # open|accepted|resolved|false_positive

@app.post("/v2/findings/{finding_id}/state")
def update_finding_state(finding_id: str, body: FindingStateIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    row = db.execute(text("SELECT tenant_id FROM findings WHERE id=:id"), {"id": finding_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    set_tenant_guc(db, row["tenant_id"])
    if body.state not in ("open","accepted","resolved","false_positive"):
        raise HTTPException(status_code=400, detail="invalid state")
    db.execute(text("UPDATE findings SET state=:s, updated_at=now() WHERE id=:id"), {"s": body.state, "id": finding_id})
    db.commit()
    return {"ok": True, "id": finding_id, "state": body.state}

def severity_rank(s: str) -> int:
    order = {"critical":4,"high":3,"medium":2,"low":1,"info":0}
    return order.get(s,0)

@app.get("/v2/reports/{run_id}.json")
def report_json(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(select(Run).where(Run.id == run_id)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r.tenant_id)
    eng = db.execute(select(Engagement).where(Engagement.id == r.engagement_id)).scalar_one()
    rows = db.execute(
        text("""
            SELECT id, title, severity, category, cwe, owasp, cvss, affected_assets, description, recommendation, state
            FROM findings WHERE run_id=:r
        """),
        {"r": run_id}
    ).mappings().all()
    findings = sorted([dict(x) for x in rows], key=lambda x: -severity_rank(x["severity"]))
    return {"run_id": run_id, "engagement": {"id": eng.id, "name": eng.name, "type": eng.type, "scope": eng.scope}, "findings": findings}

@app.get("/v2/reports/{run_id}.md")
def report_md(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    data = report_json(run_id, db, principal)
    lines = []
    lines.append(f"# Security Test Report — Run {run_id}")
    eng = data["engagement"]
    lines.append(f"**Engagement:** {eng['name']}  \\n**Type:** {eng['type']}")
    lines.append("")
    lines.append("## Findings Summary")
    if not data["findings"]:
        lines.append("_No findings reported._")
    for i, f in enumerate(data["findings"], start=1):
        lines.append(f"### {i}. {f['title']}  \\n**Severity:** {f['severity']}  \\n**Category:** {f.get('category','-')}")
        if f.get("cwe"):
            lines.append(f"- CWE: {f['cwe']}")
        if f.get("owasp"):
            lines.append(f"- OWASP: {f['owasp']}")
        if f.get("cvss") is not None:
            lines.append(f"- CVSS: {f['cvss']}")
        assets = f.get("affected_assets")
        if assets:
            lines.append(f"- Affected: `{json.dumps(assets)}`")
        if f.get("description"):
            lines.append(f"\\n**Description**\\n\\n{f['description']}")
        if f.get("recommendation"):
            lines.append(f"\\n**Recommendation**\\n\\n{f['recommendation']}")
        lines.append("")
    return "\\n".join(lines)
