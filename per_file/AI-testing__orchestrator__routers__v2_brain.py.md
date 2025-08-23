# File: AI-testing/orchestrator/routers/v2_brain.py

- Size: 3853 bytes
- Kind: text
- SHA256: 92b443cbf78e9e3cb53bf50b4e7113c5d35ebf8f458e7c917ae568332f56c7ca

## Python Imports

```
auth, datetime, db, fastapi, glob, hashlib, json, os, pathlib, sqlalchemy, tenancy, typing, uuid
```

## Head (first 60 lines)

```
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

import glob, pathlib

APP_ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG_DIR = APP_ROOT / "catalog" / "tests"
PACKS_DIR = APP_ROOT / "catalog" / "packs"

router = APIRouter()

def _load_catalog():
    items = []
    for path in glob.glob(str(CATALOG_DIR / "*.json")):
        try:
            with open(path,"r") as f:
                items.append(json.load(f))
        except Exception:
            pass
    return {"items": items}

@router.post("/v2/engagements/{engagement_id}/plan/auto")
def plan_auto(engagement_id: str, body: Dict[str, Any] = None, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(text("SELECT id, tenant_id, type, scope FROM engagements WHERE id=:id"), {"id": engagement_id}).mappings().first()
    if not e:
        raise HTTPException(status_code=404, detail="engagement not found")
    set_tenant_guc(db, e["tenant_id"])
    cat = _load_catalog()
    ids = {i.get("id") for i in cat["items"] if isinstance(i, dict)}
    sel = []
    t = (e.get("type") or "").lower()
    scope = e.get("scope") or {}
    if t in ("network","external","internal"):
        if scope.get("in_scope_cidrs"): sel += ["network_discovery_ping_sweep","network_nmap_tcp_top_1000"]
        if scope.get("in_scope_domains"): sel += ["web_owasp_top10_core"]
    if t in ("web","webapp"):
        sel += ["web_owasp_top10_core"]
    if t in ("mobile","android","ios"):
        sel += ["mobile_static_analysis_apk"]
    packs = (body or {}).get("preferences",{}).get("packs") if isinstance(body, dict) else []
    if packs:
```

## Tail (last 60 lines)

```
                items.append(json.load(f))
        except Exception:
            pass
    return {"items": items}

@router.post("/v2/engagements/{engagement_id}/plan/auto")
def plan_auto(engagement_id: str, body: Dict[str, Any] = None, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(text("SELECT id, tenant_id, type, scope FROM engagements WHERE id=:id"), {"id": engagement_id}).mappings().first()
    if not e:
        raise HTTPException(status_code=404, detail="engagement not found")
    set_tenant_guc(db, e["tenant_id"])
    cat = _load_catalog()
    ids = {i.get("id") for i in cat["items"] if isinstance(i, dict)}
    sel = []
    t = (e.get("type") or "").lower()
    scope = e.get("scope") or {}
    if t in ("network","external","internal"):
        if scope.get("in_scope_cidrs"): sel += ["network_discovery_ping_sweep","network_nmap_tcp_top_1000"]
        if scope.get("in_scope_domains"): sel += ["web_owasp_top10_core"]
    if t in ("web","webapp"):
        sel += ["web_owasp_top10_core"]
    if t in ("mobile","android","ios"):
        sel += ["mobile_static_analysis_apk"]
    packs = (body or {}).get("preferences",{}).get("packs") if isinstance(body, dict) else []
    if packs:
        for path in glob.glob(str(PACKS_DIR / "*.json")):
            try:
                with open(path,"r") as f:
                    pj = json.load(f)
                if pj.get("id") in packs:
                    sel += pj.get("tests",[])
            except Exception:
                pass
    dedup = []
    for s in sel:
        if s in ids and s not in dedup:
            dedup.append(s)
    return {"engagement_id": e["id"], "selected_tests": [{"id": s, "params": {}} for s in dedup], "explanation": "Heuristic selection + packs"}

@router.post("/v2/brain/feedback")
def brain_feedback(body: Dict[str, Any], db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant_guc(db, principal.tenant_id)
    db.execute(text("""
        INSERT INTO brain_feedback (id, tenant_id, engagement_id, plan_id, run_id, rating, comment, created_by)
        VALUES (:id,:t,:e,:p,:r,:ra,:c,NULL)
    """), {
        "id": f"fb_{uuid.uuid4().hex[:10]}",
        "t": principal.tenant_id,
        "e": body.get("engagement_id"),
        "p": body.get("plan_id"),
        "r": body.get("run_id"),
        "ra": int(body.get("rating",5)),
        "c": body.get("comment")
    })
    db.commit()
    return {"ok": True}

@router.get("/v2/brain/providers")
def brain_providers():
    return {"providers": ["heuristic"]}
```

