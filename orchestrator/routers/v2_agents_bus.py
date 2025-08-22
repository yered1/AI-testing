import os, uuid, json, datetime, hashlib
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, UploadFile, File, Form, Header, Response, Query, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..auth import Principal
from ..tenancy import set_tenant_guc, require_tenant

def month_key(dt=None):
    dt = dt or datetime.datetime.utcnow()
    return dt.strftime("%Y-%m")

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def insert_run_event(db: Session, tenant_id: str, run_id: str, ev_type: str, payload: Dict[str, Any]):
    set_tenant_guc(db, tenant_id)
    db.execute(text("INSERT INTO run_events (id, tenant_id, run_id, type, payload) VALUES (:id,:t,:r,:ty,:pl)"),
               {"id": f"ev_{uuid.uuid4().hex[:12]}", "t": tenant_id, "r": run_id, "ty": ev_type, "pl": json.dumps(payload)})
    db.commit()


router = APIRouter()

def require_agent(db: Session, tenant_id: str, agent_id: str, agent_key: str):
    set_tenant_guc(db, tenant_id)
    row = db.execute(text("SELECT id, agent_key_hash FROM agents WHERE id=:id"), {"id": agent_id}).mappings().first()
    if not row or row["agent_key_hash"] != sha256_hex(agent_key):
        raise HTTPException(status_code=401, detail="invalid agent credentials")

@router.post("/v2/agent_tokens")
def create_agent_token(body: Dict[str, Any], db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    tenant_id = body.get("tenant_id") or principal.tenant_id
    name = body.get("name","agent")
    expires_in_days = int(body.get("expires_in_days", 30))
    set_tenant_guc(db, tenant_id)
    raw = uuid.uuid4().hex + uuid.uuid4().hex
    aid = f"at_{uuid.uuid4().hex[:10]}"
    db.execute(text("INSERT INTO agent_tokens (id, tenant_id, name, token_hash, expires_at, status, created_by) VALUES (:id,:t,:n,:h, now() + (INTERVAL '1 day' * :d), 'active', NULL)"),
               {"id": aid, "t": tenant_id, "n": name, "h": sha256_hex(raw), "d": expires_in_days})
    db.commit()
    return {"id": aid, "token": raw}

@router.get("/v2/agents")
def agents_list(db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant_guc(db, principal.tenant_id)
    rows = db.execute(text("""
        SELECT id, name, kind, status, last_seen
        FROM agents
        WHERE tenant_id = current_setting('app.current_tenant', true)
        ORDER BY last_seen DESC
        LIMIT 200
    """)).mappings().all()
    return {"agents": [dict(x) for x in rows]}

@router.post("/v2/agents/register")
def agent_register(body: Dict[str, Any], x_tenant_id: str = Header(alias="X-Tenant-Id"), db: Session = Depends(get_db)):
    enroll_token = body.get("enroll_token")
    name = body.get("name","agent")
    kind = body.get("kind","cross_platform")
    set_tenant_guc(db, x_tenant_id)
    rows = db.execute(text("SELECT token_hash FROM agent_tokens WHERE tenant_id=:t AND status='active' ORDER BY created_at DESC"),
                      {"t": x_tenant_id}).mappings().all()
    th = sha256_hex(enroll_token or "")
    match = [r for r in rows if r["token_hash"] == th]
    if not match:
        raise HTTPException(status_code=401, detail="invalid enroll token")
    agent_id = f"agt_{uuid.uuid4().hex[:10]}"
    agent_key = uuid.uuid4().hex + uuid.uuid4().hex
    db.execute(text("INSERT INTO agents (id, tenant_id, name, kind, status, agent_key_hash) VALUES (:id,:t,:n,:k,'online',:h)"),
               {"id": agent_id, "t": x_tenant_id, "n": name, "k": kind, "h": sha256_hex(agent_key)})
    db.execute(text("UPDATE agent_tokens SET used_at=now() WHERE token_hash=:h"), {"h": th})
    db.commit()
    return {"agent_id": agent_id, "agent_key": agent_key}

@router.post("/v2/agents/heartbeat")
def agent_heartbeat(x_tenant_id: str = Header(alias="X-Tenant-Id"), x_agent_id: str = Header(alias="X-Agent-Id"), x_agent_key: str = Header(alias="X-Agent-Key"), db: Session = Depends(get_db)):
    require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    db.execute(text("UPDATE agents SET last_seen=now(), status='online' WHERE id=:id"), {"id": x_agent_id}); db.commit()
    return {"ok": True}

@router.post("/v2/agents/lease")
def agent_lease(body: Dict[str, Any] = None, x_tenant_id: str = Header(alias="X-Tenant-Id"), x_agent_id: str = Header(alias="X-Agent-Id"), x_agent_key: str = Header(alias="X-Agent-Key"), db: Session = Depends(get_db)):
    require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    row = db.execute(text("""
        SELECT id, run_id, plan_id, engagement_id, adapter, params FROM jobs
        WHERE tenant_id = current_setting('app.current_tenant', true)
          AND status='queued'
        ORDER BY created_at ASC
        LIMIT 1
    """)).mappings().first()
    if not row:
        return Response(status_code=204)
    db.execute(text("UPDATE jobs SET status='leased', leased_by=:a, lease_expires_at=now() + interval '5 minutes' WHERE id=:id"),
               {"a": x_agent_id, "id": row["id"]}); db.commit()
    return {"id": row["id"], "adapter": row["adapter"], "params": row["params"]}

@router.post("/v2/jobs/{job_id}/events")
def job_events(job_id: str, body: Dict[str, Any], x_tenant_id: str = Header(alias="X-Tenant-Id"), x_agent_id: str = Header(alias="X-Agent-Id"), x_agent_key: str = Header(alias="X-Agent-Key"), db: Session = Depends(get_db)):
    require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    job = db.execute(text("SELECT id, run_id FROM jobs WHERE id=:id"), {"id": job_id}).mappings().first()
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    db.execute(text("INSERT INTO job_events (id, tenant_id, job_id, type, payload) VALUES (:id,:t,:j,:ty,:pl)"),
               {"id": f"je_{uuid.uuid4().hex[:10]}", "t": x_tenant_id, "j": job_id, "ty": body.get("type","job.event"), "pl": json.dumps(body.get("payload",{}))})
    insert_run_event(db, x_tenant_id, job["run_id"], body.get("type","job.event"), body.get("payload",{}))
    return {"ok": True}

@router.post("/v2/jobs/{job_id}/complete")
def job_complete(job_id: str, body: Dict[str, Any], x_tenant_id: str = Header(alias="X-Tenant-Id"), x_agent_id: str = Header(alias="X-Agent-Id"), x_agent_key: str = Header(alias="X-Agent-Key"), db: Session = Depends(get_db)):
    require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    job = db.execute(text("SELECT id, run_id FROM jobs WHERE id=:id"), {"id": job_id}).mappings().first()
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    status = body.get("status","succeeded")
    db.execute(text("UPDATE jobs SET status=:s WHERE id=:id"), {"s": status, "id": job_id})
    insert_run_event(db, x_tenant_id, job["run_id"], f"job.{status}", body.get("result",{}))
    # finalize run if no active jobs
    cnt = db.execute(text("SELECT COUNT(*) FROM jobs WHERE run_id=:r AND status IN ('queued','leased','running')"), {"r": job["run_id"]}).scalar()
    if int(cnt or 0) == 0:
        db.execute(text("UPDATE runs SET status='completed' WHERE id=:r"), {"r": job["run_id"]})
        insert_run_event(db, x_tenant_id, job["run_id"], "run.completed", {"message":"All jobs finished"})
    db.commit()
    return {"ok": True}
