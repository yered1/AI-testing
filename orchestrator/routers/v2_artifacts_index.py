from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..auth import Principal
from ..tenancy import set_tenant_guc, require_tenant
import hashlib

router = APIRouter()

def sha256_hex(s: str) -> str:
    return hashlib.sha256((s or "").encode()).hexdigest()

def _agent_ok(db: Session, tenant_id: str, agent_id: Optional[str], agent_key: Optional[str]) -> bool:
    if not agent_id or not agent_key:
        return False
    set_tenant_guc(db, tenant_id)
    row = db.execute(text("SELECT agent_key_hash FROM agents WHERE id=:id"), {"id": agent_id}).mappings().first()
    if not row:
        return False
    return row["agent_key_hash"] == sha256_hex(agent_key)

@router.get("/v2/runs/{run_id}/artifacts/index.json")
def artifacts_index(run_id: str,
                    x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
                    x_agent_id: Optional[str] = Header(default=None, alias="X-Agent-Id"),
                    x_agent_key: Optional[str] = Header(default=None, alias="X-Agent-Key"),
                    principal: Principal = Depends(require_tenant),
                    db: Session = Depends(get_db)):
    tenant_id = x_tenant_id or principal.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant missing")
    # authenticate: agent headers or user principal
    if x_agent_id and x_agent_key:
        if not _agent_ok(db, tenant_id, x_agent_id, x_agent_key):
            raise HTTPException(status_code=401, detail="invalid agent credentials")
        set_tenant_guc(db, tenant_id)
    else:
        set_tenant_guc(db, principal.tenant_id)

    r = db.execute(text("SELECT id, tenant_id FROM runs WHERE id=:id"), {"id": run_id}).mappings().first()
    if not r:
        raise HTTPException(status_code=404, detail="run not found")
    if r["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="forbidden")

    rows = db.execute(text("""
        SELECT id, run_id, kind, label, path, created_at
        FROM artifacts
        WHERE tenant_id = current_setting('app.current_tenant', true)
          AND run_id = :r
        ORDER BY created_at ASC
    """), {"r": run_id}).mappings().all()
    return {"run_id": run_id, "artifacts": [dict(row) for row in rows]}
