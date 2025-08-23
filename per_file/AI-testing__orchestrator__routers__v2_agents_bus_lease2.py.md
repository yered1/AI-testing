# File: AI-testing/orchestrator/routers/v2_agents_bus_lease2.py

- Size: 2870 bytes
- Kind: text
- SHA256: c34e9222d5144d2e57939388585f47a7591d882555b6f6d67a3315f8f1c5235b

## Python Imports

```
db, fastapi, hashlib, sqlalchemy, tenancy, typing
```

## Head (first 60 lines)

```
from fastapi import APIRouter, Depends, Header, Response, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..tenancy import set_tenant_guc
import hashlib
from typing import List, Dict, Any, Optional

router = APIRouter()

def sha256_hex(s: str) -> str:
    return hashlib.sha256((s or "").encode()).hexdigest()

def _require_agent(db: Session, tenant_id: str, agent_id: str, agent_key: str):
    set_tenant_guc(db, tenant_id)
    row = db.execute(text("SELECT id, agent_key_hash FROM agents WHERE id=:id"),
                     {"id": agent_id}).mappings().first()
    if not row or row["agent_key_hash"] != sha256_hex(agent_key):
        raise HTTPException(status_code=401, detail="invalid agent credentials")

def adapter_to_kind(adapter: str) -> str:
    a = (adapter or "").lower()
    if a.startswith("zap_"):
        return "zap"
    if a.startswith("nuclei"):
        return "nuclei"
    if "semgrep" in a:
        return "semgrep"
    if a.startswith("mobile_") or "apk" in a:
        return "mobile_apk"
    # fallbacks
    if a.startswith("nmap") or "network" in a:
        return "network"
    return "cross_platform"

@router.post("/v2/agents/lease2")
def agent_lease2(body: Optional[Dict[str, Any]] = None,
                 x_tenant_id: str = Header(alias="X-Tenant-Id"),
                 x_agent_id: str = Header(alias="X-Agent-Id"),
                 x_agent_key: str = Header(alias="X-Agent-Key"),
                 db: Session = Depends(get_db)):
    _require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    kinds = []
    if isinstance(body, dict):
        k = body.get("kinds")
        if isinstance(k, list):
            kinds = [str(i).lower() for i in k if i]
    # Select a small window and lock to avoid races
    rows = db.execute(text("""
        SELECT id, run_id, plan_id, engagement_id, adapter, params
        FROM jobs
        WHERE tenant_id = current_setting('app.current_tenant', true)
          AND status='queued'
        ORDER BY created_at ASC
        FOR UPDATE SKIP LOCKED
        LIMIT 50
    """)).mappings().all()
    selected = None
    for r in rows:
        if kinds:
```

## Tail (last 60 lines)

```
def adapter_to_kind(adapter: str) -> str:
    a = (adapter or "").lower()
    if a.startswith("zap_"):
        return "zap"
    if a.startswith("nuclei"):
        return "nuclei"
    if "semgrep" in a:
        return "semgrep"
    if a.startswith("mobile_") or "apk" in a:
        return "mobile_apk"
    # fallbacks
    if a.startswith("nmap") or "network" in a:
        return "network"
    return "cross_platform"

@router.post("/v2/agents/lease2")
def agent_lease2(body: Optional[Dict[str, Any]] = None,
                 x_tenant_id: str = Header(alias="X-Tenant-Id"),
                 x_agent_id: str = Header(alias="X-Agent-Id"),
                 x_agent_key: str = Header(alias="X-Agent-Key"),
                 db: Session = Depends(get_db)):
    _require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    kinds = []
    if isinstance(body, dict):
        k = body.get("kinds")
        if isinstance(k, list):
            kinds = [str(i).lower() for i in k if i]
    # Select a small window and lock to avoid races
    rows = db.execute(text("""
        SELECT id, run_id, plan_id, engagement_id, adapter, params
        FROM jobs
        WHERE tenant_id = current_setting('app.current_tenant', true)
          AND status='queued'
        ORDER BY created_at ASC
        FOR UPDATE SKIP LOCKED
        LIMIT 50
    """)).mappings().all()
    selected = None
    for r in rows:
        if kinds:
            if adapter_to_kind(r["adapter"]) in kinds:
                selected = r; break
        else:
            selected = r; break
    if not selected:
        # nothing matching
        return Response(status_code=204)
    db.execute(text("""
        UPDATE jobs SET status='leased', leased_by=:a, lease_expires_at=now() + interval '5 minutes'
        WHERE id=:id
    """), {"a": x_agent_id, "id": selected["id"]})
    db.commit()
    return {
        "id": selected["id"],
        "adapter": selected["adapter"],
        "params": selected["params"],
        "run_id": selected["run_id"],
        "plan_id": selected["plan_id"],
        "engagement_id": selected["engagement_id"],
    }
```

