from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from .db import get_db
from .auth import Principal, get_principal
from .models import Membership
from sqlalchemy import select

def set_tenant_guc(db: Session, tenant_id: str):
    # Set per-connection GUC used by Postgres RLS policies
    db.execute(text('SET LOCAL "app.current_tenant" = :tenant'), {"tenant": tenant_id})

def require_tenant(principal: Principal = Depends(get_principal)):
    if not principal.tenant_id:
        raise HTTPException(status_code=403, detail="tenant not selected")
    return principal

def ensure_membership(db: Session, principal: Principal, tenant_id: str):
    # Ensure the principal belongs to the tenant
    from .models import Membership
    mem = db.execute(select(Membership).where(Membership.user_id == principal.user_id, Membership.tenant_id == tenant_id)).scalar_one_or_none()
    if not mem:
        raise HTTPException(status_code=403, detail="not a member of tenant")
    return mem
