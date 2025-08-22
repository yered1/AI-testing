import hashlib, json, uuid, pathlib, glob, datetime, os, asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, text
import httpx, requests
from sse_starlette.sse import EventSourceResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .db import get_db, SessionLocal
from .models import Engagement, Plan, Run
from .auth import get_principal, Principal
from .tenancy import set_tenant_guc, require_tenant, ensure_membership
from .brain import Brain

APP_ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_DIR = APP_ROOT / "catalog" / "tests"
TEMPLATE_DIR = pathlib.Path(__file__).resolve().parent / "templates"
OPA_URL = os.environ.get("OPA_URL","http://localhost:8181/v1/data/pentest/policy")
SIMULATE = os.environ.get("SIMULATE_PROGRESS","false").lower() == "true"
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")
EVIDENCE_DIR = os.environ.get("EVIDENCE_DIR", "/data/evidence")

env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(enabled_extensions=("html",))
)

app = FastAPI(title="AI Testing Orchestrator (v2)", version="0.7.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def set_tenant(db: Session, tenant_id: str):
    set_tenant_guc(db, tenant_id)

def load_catalog() -> Dict[str, Any]:
    items = []
    for path in glob.glob(str(CATALOG_DIR / "*.json")):
        with open(path, "r") as f:
            items.append(json.load(f))
    return {"version": "0.1.0", "items": items}

# ---- Auto-plan ----
class AutoPlanIn(BaseModel):
    preferences: Dict[str, Any] = Field(default_factory=dict)  # e.g., {"packs":["pack.web_owasp_core"]}
    risk_tier: str = "safe_active"

@app.post("/v2/engagements/{engagement_id}/plan/auto")
def plan_auto(engagement_id: str, body: AutoPlanIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(select(Engagement).where(Engagement.id == engagement_id)).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="engagement not found")
    set_tenant(db, e.tenant_id)

    catalog = load_catalog()
    brain = Brain()
    br = brain.suggest({"id": e.id, "type": e.type, "scope": e.scope}, catalog)

    # apply packs from preferences
    packs = body.preferences.get("packs") or []
    pack_tests = []
    if packs:
        # simple pack map (keep consistent with /v1/catalog/packs)
        pack_map = {
            "pack.standard_network":["network.discovery.ping_sweep","network.nmap.tcp_top_1000"],
            "pack.web_owasp_core":["web.owasp.top10.core"]
        }
        for pid in packs:
            pack_tests += pack_map.get(pid, [])
    selected = list(dict.fromkeys(br.tests + pack_tests))

    # policy filter (intrusive check delegated to OPA; we simply pass through risk tier)
    opa_input = {"risk_tier": body.risk_tier, "scope": e.scope, "approval_granted": False}
    denies = []
    try:
        import requests as _req
        r = _req.post(OPA_URL, json={"input": opa_input}, timeout=3)
        r.raise_for_status()
        denies = r.json().get("result",{}).get("deny",[])
    except Exception:
        pass

    return {
        "engagement_id": e.id,
        "selected_tests": [{"id": tid, "params": {}} for tid in selected],
        "explanation": br.explanation,
        "policy_denies": denies
    }

# ---- Feedback ----
class FeedbackIn(BaseModel):
    engagement_id: Optional[str] = None
    plan_id: Optional[str] = None
    run_id: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

@app.post("/v2/brain/feedback")
def brain_feedback(body: FeedbackIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    tenant_id = principal.tenant_id
    set_tenant(db, tenant_id)
    db.execute(text("""
        INSERT INTO brain_feedback (id, tenant_id, engagement_id, plan_id, run_id, rating, comment, created_by)
        VALUES (:id,:t,:e,:p,:r,:ra,:c,:u)
    """), {"id": f"fb_{uuid.uuid4().hex[:10]}", "t": tenant_id, "e": body.engagement_id, "p": body.plan_id, "r": body.run_id, "ra": body.rating, "c": body.comment, "u": principal.user_id})
    db.commit()
    return {"ok": True}

@app.get("/v2/brain/providers")
def brain_providers():
    return {"provider": os.environ.get("LLM_PROVIDER","heuristic"), "http_endpoint": bool(os.environ.get("LLM_HTTP_ENDPOINT"))}
