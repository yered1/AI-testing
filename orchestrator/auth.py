import uuid
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import JWTError
from .settings import settings
from .db import get_db
from sqlalchemy.orm import Session
from .models import User, Tenant, Membership, Role
from sqlalchemy import select

bearer = HTTPBearer(auto_error=False)

class Principal:
    def __init__(self, user_id: str, email: str, name: str, tenant_id: Optional[str], role: Optional[Role], raw_claims: Dict[str,Any]):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.tenant_id = tenant_id
        self.role = role
        self.claims = raw_claims

def _dev_principal(req: Request, db: Session) -> Principal:
    user = req.headers.get("X-Dev-User", "dev-user")
    email = req.headers.get("X-Dev-Email", "dev@example.com")
    tenant = req.headers.get("X-Tenant-Id", "t_demo")
    # ensure tenant/user/membership exist
    tu = db.execute(select(Tenant).where(Tenant.id == tenant)).scalar_one_or_none()
    if not tu:
        db.add(Tenant(id=tenant, name=f"Tenant {tenant}"))
    # find or create user by subject
    subject = f"dev:{user}"
    u = db.execute(select(User).where(User.subject == subject)).scalar_one_or_none()
    if not u:
        u = User(id=str(uuid.uuid4()), subject=subject, email=email, name=user)
        db.add(u)
    # membership
    m = db.execute(select(Membership).where(Membership.tenant_id == tenant, Membership.user_id == u.id)).scalar_one_or_none()
    if not m:
        m = Membership(id=str(uuid.uuid4()), tenant_id=tenant, user_id=u.id, role=Role.PROJECT_MANAGER)
        db.add(m)
    db.commit()
    return Principal(user_id=u.id, email=u.email, name=u.name, tenant_id=tenant, role=m.role, raw_claims={"mode":"dev"})

def _verify_oidc(token: str) -> Dict[str,Any]:
    # For simplicity, accept unsigned dev tokens if issuer unset.
    if not settings.oidc_issuer:
        try:
            return jwt.get_unverified_claims(token)
        except JWTError as e:
            raise HTTPException(status_code=401, detail=f"invalid token: {e}")
    # In production, fetch JWKS from OIDC_ISSUER and verify. (Left as a stub for brevity.)
    try:
        claims = jwt.get_unverified_claims(token)
        return claims
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"invalid token: {e}")

def get_principal(request: Request, db: Session = Depends(get_db), creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer)) -> Principal:
    if settings.dev_bypass_auth:
        return _dev_principal(request, db)
    if not creds:
        raise HTTPException(status_code=401, detail="missing bearer token")
    claims = _verify_oidc(creds.credentials)
    # mfa requirement
    if settings.require_mfa:
        amr = claims.get("amr", [])
        if "mfa" not in amr and "otp" not in amr:
            raise HTTPException(status_code=403, detail="MFA required")
    sub = claims.get("sub")
    email = claims.get("email","")
    name = claims.get("name","")
    if not sub:
        raise HTTPException(status_code=401, detail="token missing sub")
    # ensure user exists
    u = db.execute(select(User).where(User.subject == sub)).scalar_one_or_none()
    if not u:
        u = User(id=str(uuid.uuid4()), subject=sub, email=email, name=name)
        db.add(u); db.commit()
    # tenant selection: prefer X-Tenant-Id header; else first membership
    tenant = request.headers.get("X-Tenant-Id")
    if not tenant:
        mem = db.execute(select(Membership).where(Membership.user_id == u.id)).scalar_one_or_none()
        tenant = mem.tenant_id if mem else None
    role = None
    if tenant:
        mem = db.execute(select(Membership).where(Membership.user_id == u.id, Membership.tenant_id == tenant)).scalar_one_or_none()
        if mem:
            role = mem.role
    return Principal(user_id=u.id, email=u.email, name=u.name, tenant_id=tenant, role=role, raw_claims=claims)
