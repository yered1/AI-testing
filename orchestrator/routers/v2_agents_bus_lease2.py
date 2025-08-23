
from fastapi import APIRouter, Depends, Header, Response, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from ..db import get_db
from ..tenancy import set_tenant_guc
import hashlib, datetime

router = APIRouter()

def sha256_hex(s: str) -> str:
    import hashlib as _h
    return _h.sha256((s or "").encode()).hexdigest()

def _require_agent(db: Session, tenant_id: str, agent_id: str, agent_key: str):
    set_tenant_guc(db, tenant_id)
    row = db.execute(text("SELECT id, agent_key_hash, status FROM agents WHERE id=:id"),
                     {"id": agent_id}).mappings().first()
    if not row or row["agent_key_hash"] != sha256_hex(agent_key):
        raise HTTPException(status_code=401, detail="invalid agent credentials")
    # Update last_seen
    db.execute(text("UPDATE agents SET last_seen=now(), status='online' WHERE id=:id"), {"id": agent_id})
    db.commit()

def _adapter_kind(adapter: str) -> str:
    # map "semgrep_default" -> "semgrep", "zap_baseline"->"zap", "nuclei_default"->"nuclei"
    if not adapter:
        return ""
    return (adapter.split("_", 1)[0] or "").lower()

@router.post("/v2/agents/lease2")
def agent_lease2(
    kinds: Optional[List[str]] = None,
    x_tenant_id: str = Header(alias="X-Tenant-Id"),
    x_agent_id: str = Header(alias="X-Agent-Id"),
    x_agent_key: str = Header(alias="X-Agent-Key"),
    db: Session = Depends(get_db)
):
    """
    Enhanced leasing endpoint that returns run/plan/engagement context.
    Agents may optionally send a JSON body like {"kinds":["semgrep","zap"]}.
    """
    # FastAPI will pass body params only if declared; emulate optional body
    # by reading directly if needed (compat with agents that send no body).
    _require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    set_tenant_guc(db, x_tenant_id)

    # Fetch a few queued jobs and filter in Python to respect 'kinds'
    rows = db.execute(text("""
        SELECT id, run_id, plan_id, engagement_id, adapter, params
        FROM jobs
        WHERE tenant_id = current_setting('app.current_tenant', true)
          AND status='queued'
        ORDER BY created_at ASC
        FOR UPDATE SKIP LOCKED
        LIMIT 50
    """)).mappings().all()

    if not rows:
        return Response(status_code=204)

    kinds_set = {k.lower() for k in (kinds or [])}
    chosen = None
    if kinds_set:
        for r in rows:
            if _adapter_kind(r["adapter"]) in kinds_set:
                chosen = r; break
    else:
        # No kinds specified: choose the first
        chosen = rows[0]

    if not chosen:
        # No matching job found
        return Response(status_code=204)

    db.execute(text("""
        UPDATE jobs
        SET status='leased',
            leased_by=:a,
            lease_expires_at=now() + interval '10 minutes'
        WHERE id=:id
    """), {"a": x_agent_id, "id": chosen["id"]})
    db.commit()

    return {
        "id": chosen["id"],
        "adapter": chosen["adapter"],
        "params": chosen["params"],
        "run_id": chosen["run_id"],
        "plan_id": chosen["plan_id"],
        "engagement_id": chosen["engagement_id"]
    }
