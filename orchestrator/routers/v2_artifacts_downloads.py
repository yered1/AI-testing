import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..auth import Principal
from ..tenancy import set_tenant_guc, require_tenant

router = APIRouter()

def _check_agent(db: Session, tenant_id: str, agent_id: str, agent_key: str) -> bool:
    set_tenant_guc(db, tenant_id)
    row = db.execute(text("SELECT agent_key_hash FROM agents WHERE id=:id"), {"id": agent_id}).mappings().first()
    if not row:
        return False
    import hashlib
    return row["agent_key_hash"] == hashlib.sha256(agent_key.encode()).hexdigest()

@router.get("/v2/artifacts/{artifact_id}/download")
def artifact_download(artifact_id: str,
                      x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
                      x_agent_id: Optional[str] = Header(default=None, alias="X-Agent-Id"),
                      x_agent_key: Optional[str] = Header(default=None, alias="X-Agent-Key"),
                      principal: Principal = Depends(require_tenant),
                      db: Session = Depends(get_db)):

    # Determine tenant: prefer agent header or principal
    tenant_id = x_tenant_id or principal.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant missing")

    # Agent-auth path (agents may not have user principal)
    if x_agent_id and x_agent_key:
        if not _check_agent(db, tenant_id, x_agent_id, x_agent_key):
            raise HTTPException(status_code=401, detail="invalid agent credentials")
        set_tenant_guc(db, tenant_id)
    else:
        # User-auth path
        set_tenant_guc(db, principal.tenant_id)

    row = db.execute(text("SELECT id, tenant_id, run_id, label, kind, path FROM artifacts WHERE id=:id"),
                     {"id": artifact_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="artifact not found")
    if row["tenant_id"] != tenant_id:
        # prevent cross-tenant
        raise HTTPException(status_code=403, detail="forbidden")

    path = row["path"]
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="artifact file missing")

    data = None
    with open(path, "rb") as f:
        data = f.read()
    filename = f"{artifact_id}_{os.path.basename(path)}"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    # best-effort content type by extension
    mt = "application/octet-stream"
    if path.endswith(".json"): mt = "application/json"
    if path.endswith(".html"): mt = "text/html"
    if path.endswith(".txt"): mt = "text/plain"
    if path.endswith(".zip"): mt = "application/zip"
    return Response(content=data, media_type=mt, headers=headers)
