from fastapi import APIRouter, Depends, Header, Response, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..tenancy import set_tenant_guc
import hashlib

router = APIRouter()

def sha256_hex(s: str) -> str:
    return hashlib.sha256((s or "").encode()).hexdigest()

def _require_agent(db: Session, tenant_id: str, agent_id: str, agent_key: str):
    set_tenant_guc(db, tenant_id)
    row = db.execute(text("SELECT id, agent_key_hash FROM agents WHERE id=:id"),
                     {"id": agent_id}).mappings().first()
    if not row or row["agent_key_hash"] != sha256_hex(agent_key):
        raise HTTPException(status_code=401, detail="invalid agent credentials")

@router.post("/v2/agents/lease2")
def agent_lease2(x_tenant_id: str = Header(alias="X-Tenant-Id"),
                 x_agent_id: str = Header(alias="X-Agent-Id"),
                 x_agent_key: str = Header(alias="X-Agent-Key"),
                 db: Session = Depends(get_db)):
    _require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    row = db.execute(text("""
        SELECT id, run_id, plan_id, engagement_id, adapter, params
        FROM jobs
        WHERE tenant_id = current_setting('app.current_tenant', true)
          AND status='queued'
        ORDER BY created_at ASC
        LIMIT 1
    """)).mappings().first()
    if not row:
        return Response(status_code=204)
    db.execute(text("""
        UPDATE jobs SET status='leased', leased_by=:a, lease_expires_at=now() + interval '5 minutes'
        WHERE id=:id
    """), {"a": x_agent_id, "id": row["id"]})
    db.commit()
    return {
        "id": row["id"],
        "adapter": row["adapter"],
        "params": row["params"],
        "run_id": row["run_id"],
        "plan_id": row["plan_id"],
        "engagement_id": row["engagement_id"]
    }
