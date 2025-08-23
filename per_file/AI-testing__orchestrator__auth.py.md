# File: AI-testing/orchestrator/auth.py

- Size: 2953 bytes
- Kind: text
- SHA256: 13362d617904f01ec628edf2bbf7d7d55e9409e49d8d8a8bb8fc2f4c337f56dc

## Python Imports

```
db, fastapi, jose, models, settings, sqlalchemy, typing, uuid
```

## Head (first 60 lines)

```
import uuid
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from sqlalchemy import select
from .settings import settings
from .db import get_db
from .models import User, Membership, Role

bearer = HTTPBearer(auto_error=False)

class Principal:
    def __init__(self, user_id: str, email: str, name: str, tenant_id: Optional[str], role: Optional[Role], raw_claims: Dict[str, Any]):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.tenant_id = tenant_id
        self.role = role
        self.raw_claims = raw_claims

def get_principal(request: Request, creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer), db: Session = Depends(get_db)) -> 'Principal':
    # Development shortcut via headers (never enable in prod)
    dev_user = request.headers.get("X-Dev-User")
    dev_email = request.headers.get("X-Dev-Email")
    if settings.dev_bypass_auth and dev_user and dev_email:
        sub = f"dev:{dev_email}"
        claims: Dict[str, Any] = {"sub": sub, "email": dev_email, "name": dev_user}
    else:
        if not creds or creds.scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="missing bearer token")
        token = creds.credentials
        try:
            # If OIDC is configured, validate audience/issuer. Otherwise, decode without verification.
            if settings.oidc_issuer and settings.oidc_audience:
                # NOTE: A real implementation must verify signatures with the issuer's JWKS.
                claims = jwt.get_unverified_claims(token)
                if claims.get("iss") != settings.oidc_issuer or settings.oidc_audience not in (claims.get("aud") or []):
                    raise JWTError("issuer/audience mismatch")
            else:
                claims = jwt.get_unverified_claims(token)
        except JWTError as e:
            raise HTTPException(status_code=401, detail=f"invalid token: {e}")
    sub = claims.get("sub")
    email = claims.get("email") or dev_email or ""
    name = claims.get("name") or dev_user or ""
    if not sub:
        raise HTTPException(status_code=401, detail="token missing sub")
    u = db.execute(select(User).where(User.subject == sub)).scalar_one_or_none()
    if not u:
        u = User(id=str(uuid.uuid4()), subject=sub, email=email, name=name)
        db.add(u); db.commit()
    tenant = request.headers.get("X-Tenant-Id") or request.headers.get("X-Tenant") or None
    role: Optional[Role] = None
    if tenant:
        mem = db.execute(select(Membership).where(Membership.user_id == u.id, Membership.tenant_id == tenant)).scalar_one_or_none()
        if mem:
            role = mem.role
    return Principal(user_id=u.id, email=u.email, name=u.name, tenant_id=tenant, role=role, raw_claims=claims)
```

