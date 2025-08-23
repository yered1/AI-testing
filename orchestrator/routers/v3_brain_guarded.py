from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from ..brain.plan_engine import plan as engine_plan

router = APIRouter()

class PlanReq(BaseModel):
    engagement_type: str = Field(..., description="web|network|code|mobile")
    scope: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    allow_intrusive: bool = False

@router.post("/v3/brain/plan/guarded")
async def guarded_plan(req: Request, body: PlanReq):
    tenant = body.tenant_id or req.headers.get("X-Tenant-Id") or "t_demo"
    plan = engine_plan(body.scope, body.engagement_type, tenant, body.preferences or {})
    approval_required = (plan.get("risk_tier") == "intrusive") and (not body.allow_intrusive)
    return {
        "selected_tests": plan.get("selected_tests", []),
        "params": plan.get("params", {}),
        "risk_tier": plan.get("risk_tier"),
        "approval_required": approval_required,
        "explanation": plan.get("explanation",""),
    }

class CacheClearReq(BaseModel):
    fp: Optional[str] = None  # reserved
    all: bool = True

@router.post("/v3/brain/cache/clear")
async def cache_clear(_: Request, body: CacheClearReq):
    # Simple cache clear: rotate file (no-op if not exists)
    import os
    path = os.environ.get("BRAIN_CACHE_PATH","/data/brain_cache.jsonl")
    try:
        if os.path.exists(path):
            os.replace(path, path + ".bak")
            return {"ok": True, "rotated": True}
    except Exception:
        pass
    return {"ok": True, "rotated": False}
