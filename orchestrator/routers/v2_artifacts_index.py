
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from ..db import get_db
from ..auth import Principal
from ..tenancy import set_tenant_guc, require_tenant

router = APIRouter()

@router.get("/v2/runs/{run_id}/artifacts/index.json")
def artifacts_index(
    run_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_tenant),
    x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
):
    """
    Return a simple JSON index of artifacts for a run.
    Agents call this to discover inputs produced by earlier steps.
    Supports both user-auth (via Principal) and explicit X-Tenant-Id header (for agent contexts behind proxies).
    """
    # Prefer authenticated principal's tenant; fall back to header (mainly for agents).
    tenant_id = principal.tenant_id or x_tenant_id
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant missing")

    set_tenant_guc(db, tenant_id)
    row = db.execute(
        text("SELECT id FROM runs WHERE id=:id AND tenant_id = current_setting('app.current_tenant', true)"),
        {"id": run_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="run not found")

    arts = db.execute(
        text(
            """
            SELECT id, run_id, kind, label, path, linked_finding_id, created_at
            FROM artifacts
            WHERE run_id=:r
            ORDER BY created_at ASC
            """
        ),
        {"r": run_id},
    ).mappings().all()

    return {"artifacts": [dict(a) for a in arts]}
