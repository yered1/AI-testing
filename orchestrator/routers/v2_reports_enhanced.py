import os, json
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..auth import Principal
from ..tenancy import set_tenant_guc, require_tenant
from ..reports.render import render_html, render_md, render_pdf

router = APIRouter()
TEMPLATE_DIR = os.environ.get("REPORT_TEMPLATES_DIR") or os.path.join(os.path.dirname(os.path.dirname(__file__)), "report_templates")
REPORTER_URL = os.environ.get("REPORTER_URL")  # e.g. http://reporter:8080

def _report_data(db: Session, run_id: str) -> Dict[str, Any]:
    r = db.execute(text("SELECT tenant_id, plan_id, engagement_id FROM runs WHERE id=:id"), {"id": run_id}).mappings().first()
    if not r:
        raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r["tenant_id"])
    eng = db.execute(text("SELECT name, type, scope FROM engagements WHERE id=:id"), {"id": r["engagement_id"]}).mappings().first()
    plan = db.execute(text("SELECT data FROM plans WHERE id=:id"), {"id": r["plan_id"]}).mappings().first()
    fnds = db.execute(text("SELECT id, title, severity, description, assets, recommendation, tags FROM findings WHERE run_id=:r"), {"r": run_id}).mappings().all()
    arts = db.execute(text("SELECT id, kind, label, path FROM artifacts WHERE run_id=:r ORDER BY created_at ASC"), {"r": run_id}).mappings().all()
    return {"run_id": run_id, "engagement": dict(eng) if eng else {}, "plan": (plan or {}).get("data", {}), "findings": [dict(x) for x in fnds], "artifacts": [dict(a) for a in arts]}

@router.get("/v2/reports/enhanced/run/{run_id}.html")
def enhanced_html(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    data = _report_data(db, run_id)
    html = render_html(TEMPLATE_DIR, data)
    return Response(html, media_type="text/html")

@router.get("/v2/reports/enhanced/run/{run_id}.md")
def enhanced_md(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    data = _report_data(db, run_id)
    md = render_md(TEMPLATE_DIR, data)
    return Response(md, media_type="text/markdown")

@router.get("/v2/reports/enhanced/run/{run_id}.pdf")
def enhanced_pdf(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    if not REPORTER_URL:
        raise HTTPException(status_code=424, detail="REPORTER_URL not configured; start the reporter service and set env REPORTER_URL")
    data = _report_data(db, run_id)
    html = render_html(TEMPLATE_DIR, data)
    try:
        pdf = render_pdf(REPORTER_URL, html, title=f"Run {run_id}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Reporter error: {e}")
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="run_{run_id}.pdf"'})

@router.get("/v2/reports/taxonomy")
def taxonomy():
    from ..reports.taxonomy import OWASP_2021, SEVERITY_ORDER
    return {"owasp_2021": OWASP_2021, "severity_order": SEVERITY_ORDER}
