# File: AI-testing/orchestrator/tenancy.py

- Size: 873 bytes
- Kind: text
- SHA256: d5ddc6b021a3fe42a2309690288089fe8b2950b8a81cd6b5d672ba124721943e

## Python Imports

```
auth, db, fastapi, models, sqlalchemy
```

## Head (first 60 lines)

```
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, select
from .db import get_db
from .auth import Principal, get_principal
from .models import Membership

def set_tenant_guc(db: Session, tenant_id: str):
    db.execute(text('SET LOCAL "app.current_tenant" = :tenant'), {"tenant": tenant_id})

def require_tenant(principal: Principal = Depends(get_principal)):
    if not principal.tenant_id:
        raise HTTPException(status_code=403, detail="tenant not selected")
    return principal

def ensure_membership(db: Session, principal: Principal, tenant_id: str):
    mem = db.execute(select(Membership).where(Membership.user_id == principal.user_id, Membership.tenant_id == tenant_id)).scalar_one_or_none()
    if not mem:
        raise HTTPException(status_code=403, detail="not a member of tenant")
    return mem
```

