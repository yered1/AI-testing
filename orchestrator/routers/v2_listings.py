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

@router.get("/v2/runs/recent")
def runs_recent(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant_guc(db, principal.tenant_id)
    rows = db.execute(text("""
        SELECT r.id, r.engagement_id, r.plan_id, r.status, COALESCE(r.created_at, now()) AS created_at
        FROM runs r
        WHERE r.tenant_id = current_setting('app.current_tenant', true)
        ORDER BY created_at DESC
        LIMIT :lim
    """), {"lim": limit}).mappings().all()
    return {"runs": [dict(x) for x in rows]}
