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

@router.post("/v2/quotas")
def quotas_set(body: Dict[str, Any], db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    tenant_id = body.get("tenant_id") or principal.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id required")
    set_tenant_guc(db, tenant_id)
    monthly_budget = int(body.get("monthly_budget", 100))
    per_plan_cap = int(body.get("per_plan_cap", 30))
    db.execute(text("""
        INSERT INTO quotas (tenant_id, month_key, monthly_budget, per_plan_cap)
        VALUES (:t, :m, :mb, :pp)
        ON CONFLICT (tenant_id, month_key) DO UPDATE SET monthly_budget=:mb, per_plan_cap=:pp
    """), {"t": tenant_id, "m": month_key(), "mb": monthly_budget, "pp": per_plan_cap})
    db.commit()
    return {"ok": True}

@router.get("/v2/quotas/{tenant_id}")
def quotas_get(tenant_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant_guc(db, tenant_id)
    row = db.execute(text("SELECT tenant_id, month_key, monthly_budget, per_plan_cap FROM quotas WHERE tenant_id=:t AND month_key=:m"),
                     {"t": tenant_id, "m": month_key()}).mappings().first()
    if not row:
        return {"tenant_id": tenant_id, "month_key": month_key(), "monthly_budget": 100, "per_plan_cap": 30}
    return dict(row)

@router.post("/v2/approvals")
def approvals_create(body: Dict[str, Any], db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    tenant_id = body.get("tenant_id") or principal.tenant_id
    engagement_id = body.get("engagement_id")
    reason = body.get("reason","")
    if not (tenant_id and engagement_id):
        raise HTTPException(status_code=400, detail="tenant_id and engagement_id required")
    set_tenant_guc(db, tenant_id)
    aid = f"ap_{uuid.uuid4().hex[:10]}"
    db.execute(text("INSERT INTO approvals (id, tenant_id, engagement_id, status, reason) VALUES (:id,:t,:e,'pending',:r)"),
               {"id": aid, "t": tenant_id, "e": engagement_id, "r": reason})
    db.commit()
    return {"id": aid, "status": "pending"}

@router.post("/v2/approvals/{approval_id}/decide")
def approvals_decide(approval_id: str, body: Dict[str, Any], db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    tenant_id = body.get("tenant_id") or principal.tenant_id
    decision = body.get("decision")
    if decision not in ("approved","denied"):
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'denied'")
    set_tenant_guc(db, tenant_id)
    db.execute(text("UPDATE approvals SET status=:s, decided_at=now() WHERE id=:id"), {"s": decision, "id": approval_id})
    db.commit()
    return {"ok": True}

@router.get("/v2/approvals")
def approvals_list(engagement_id: Optional[str] = None, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant_guc(db, principal.tenant_id)
    if engagement_id:
        rows = db.execute(text("""
            SELECT id, tenant_id, engagement_id, status, reason, created_at, decided_at
            FROM approvals
            WHERE tenant_id = current_setting('app.current_tenant', true) AND engagement_id=:e
            ORDER BY created_at DESC LIMIT 100
        """), {"e": engagement_id}).mappings().all()
    else:
        rows = db.execute(text("""
            SELECT id, tenant_id, engagement_id, status, reason, created_at, decided_at
            FROM approvals
            WHERE tenant_id = current_setting('app.current_tenant', true)
            ORDER BY created_at DESC LIMIT 100
        """)).mappings().all()
    return {"approvals": [dict(r) for r in rows]}
