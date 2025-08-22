from fastapi import APIRouter, Depends, Header, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..tenancy import set_tenant_guc
import os, uuid, hashlib

router = APIRouter()
EVIDENCE_DIR = os.environ.get("EVIDENCE_DIR","/data/evidence")

def sha256_hex(s: str) -> str:
    import hashlib
    return hashlib.sha256((s or "").encode()).hexdigest()

def _require_agent(db: Session, tenant_id: str, agent_id: str, agent_key: str):
    set_tenant_guc(db, tenant_id)
    row = db.execute(text("SELECT id, agent_key_hash FROM agents WHERE id=:id"),
                     {"id": agent_id}).mappings().first()
    if not row or row["agent_key_hash"] != sha256_hex(agent_key):
        raise HTTPException(status_code=401, detail="invalid agent credentials")

@router.post("/v2/jobs/{job_id}/artifacts")
async def job_artifacts_upload(job_id: str,
                               file: UploadFile = File(...),
                               label: str = Form("evidence"),
                               kind: str = Form("generic"),
                               x_tenant_id: str = Header(alias="X-Tenant-Id"),
                               x_agent_id: str = Header(alias="X-Agent-Id"),
                               x_agent_key: str = Header(alias="X-Agent-Key"),
                               db: Session = Depends(get_db)):
    _require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    # look up job -> run
    job = db.execute(text("SELECT run_id FROM jobs WHERE id=:id"),
                     {"id": job_id}).mappings().first()
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    run_id = job["run_id"]
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    fname = f"{run_id}_{uuid.uuid4().hex[:8]}_{file.filename}"
    path = os.path.join(EVIDENCE_DIR, fname)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    db.execute(text("""
        INSERT INTO artifacts (id, tenant_id, run_id, kind, label, path)
        VALUES (:id, current_setting('app.current_tenant', true), :r, :k, :l, :p)
    """), {"id": f"art_{uuid.uuid4().hex[:10]}", "r": run_id, "k": kind, "l": label, "p": path})
    db.commit()
    return {"ok": True, "run_id": run_id, "path": path}
