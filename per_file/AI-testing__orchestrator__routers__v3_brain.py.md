# File: AI-testing/orchestrator/routers/v3_brain.py

- Size: 3973 bytes
- Kind: text
- SHA256: 90166f00096cf434ba0fc2bd50c6327e9d6ca3ca0e5b0825f4b3fffd9c04afa9

## Python Imports

```
auth, brain, datetime, db, fastapi, json, os, sqlalchemy, tenancy, typing, uuid
```

## Head (first 60 lines)

```
import os, json, uuid, datetime as dt
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db
from ..auth import Principal
from ..tenancy import set_tenant_guc, require_tenant
from ..brain.providers.base import load_provider, list_providers

router = APIRouter()

def _engagement(db: Session, engagement_id: str):
    row = db.execute(text("SELECT id, tenant_id, name, type, scope FROM engagements WHERE id=:id"),
                     {"id": engagement_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="engagement not found")
    return dict(row)

def _try_log(db: Session, tenant_id: str, engagement_id: str, provider: str, action: str, prompt: dict, response: dict):
    try:
        set_tenant_guc(db, tenant_id)
        db.execute(text("""
            INSERT INTO brain_traces (id, tenant_id, engagement_id, provider, action, prompt, response)
            VALUES (:id,:t,:e,:p,:a,:pr,:re)
        """), {"id": f"bt_{uuid.uuid4().hex[:10]}", "t": tenant_id, "e": engagement_id,
                 "p": provider, "a": action, "pr": json.dumps(prompt), "re": json.dumps(response)})
        db.commit()
    except Exception:
        db.rollback()

@router.get("/v3/brain/providers")
def providers():
    return {"providers": list_providers()}

@router.post("/v3/brain/plan")
def brain_plan(body: Dict[str, Any] = Body(...),
               db: Session = Depends(get_db),
               principal: Principal = Depends(require_tenant)):
    engagement_id = body.get("engagement_id")
    provider_name = body.get("provider") or os.environ.get("BRAIN_PROVIDER","heuristic")
    preferences = body.get("preferences") or {}
    if not engagement_id:
        raise HTTPException(status_code=400, detail="engagement_id required")
    e = _engagement(db, engagement_id)
    set_tenant_guc(db, e["tenant_id"])
    prov = load_provider(provider_name)
    plan = prov.plan(e, e.get("scope") or {}, preferences)
    _try_log(db, e["tenant_id"], e["id"], prov.name, "plan",
             {"engagement": {"id": e["id"], "type": e.get("type")}, "preferences": preferences}, plan)
    return {"engagement_id": e["id"], "provider": prov.name, **plan}

@router.post("/v3/brain/enrich")
def brain_enrich(body: Dict[str, Any] = Body(...),
                 db: Session = Depends(get_db),
                 principal: Principal = Depends(require_tenant)):
    engagement_id = body.get("engagement_id")
    provider_name = body.get("provider") or os.environ.get("BRAIN_PROVIDER","heuristic")
    selected_tests = body.get("selected_tests") or []
    if not engagement_id:
```

## Tail (last 60 lines)

```
            VALUES (:id,:t,:e,:p,:a,:pr,:re)
        """), {"id": f"bt_{uuid.uuid4().hex[:10]}", "t": tenant_id, "e": engagement_id,
                 "p": provider, "a": action, "pr": json.dumps(prompt), "re": json.dumps(response)})
        db.commit()
    except Exception:
        db.rollback()

@router.get("/v3/brain/providers")
def providers():
    return {"providers": list_providers()}

@router.post("/v3/brain/plan")
def brain_plan(body: Dict[str, Any] = Body(...),
               db: Session = Depends(get_db),
               principal: Principal = Depends(require_tenant)):
    engagement_id = body.get("engagement_id")
    provider_name = body.get("provider") or os.environ.get("BRAIN_PROVIDER","heuristic")
    preferences = body.get("preferences") or {}
    if not engagement_id:
        raise HTTPException(status_code=400, detail="engagement_id required")
    e = _engagement(db, engagement_id)
    set_tenant_guc(db, e["tenant_id"])
    prov = load_provider(provider_name)
    plan = prov.plan(e, e.get("scope") or {}, preferences)
    _try_log(db, e["tenant_id"], e["id"], prov.name, "plan",
             {"engagement": {"id": e["id"], "type": e.get("type")}, "preferences": preferences}, plan)
    return {"engagement_id": e["id"], "provider": prov.name, **plan}

@router.post("/v3/brain/enrich")
def brain_enrich(body: Dict[str, Any] = Body(...),
                 db: Session = Depends(get_db),
                 principal: Principal = Depends(require_tenant)):
    engagement_id = body.get("engagement_id")
    provider_name = body.get("provider") or os.environ.get("BRAIN_PROVIDER","heuristic")
    selected_tests = body.get("selected_tests") or []
    if not engagement_id:
        raise HTTPException(status_code=400, detail="engagement_id required")
    e = _engagement(db, engagement_id)
    set_tenant_guc(db, e["tenant_id"])
    prov = load_provider(provider_name)
    res = prov.enrich(e, selected_tests, e.get("scope") or {})
    _try_log(db, e["tenant_id"], e["id"], prov.name, "enrich",
             {"engagement": {"id": e["id"]}, "selected_tests": selected_tests}, res)
    return {"engagement_id": e["id"], "provider": prov.name, **res}

@router.post("/v3/brain/learn")
def brain_learn(body: Dict[str, Any] = Body(...),
                db: Session = Depends(get_db),
                principal: Principal = Depends(require_tenant)):
    e = _engagement(db, body.get("engagement_id"))
    set_tenant_guc(db, e["tenant_id"])
    db.execute(text("""
        INSERT INTO brain_feedback (id, tenant_id, engagement_id, plan_id, run_id, rating, comment, labels)
        VALUES (:id,:t,:e,:p,:r,:ra,:c,:la)
    """), {"id": f"fb_{uuid.uuid4().hex[:10]}","t": e["tenant_id"],"e": e["id"],
             "p": body.get("plan_id"), "r": body.get("run_id"),
             "ra": int(body.get("rating",5)), "c": body.get("comment"),
             "la": json.dumps(body.get("labels") or [])})
    db.commit()
    return {"ok": True}
```

