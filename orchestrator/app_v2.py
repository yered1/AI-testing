# v2 extensions: quotas + approvals + opa enforcement
# (This file replaces/overlays orchestrator/app_v2.py from Batch 2.)

import hashlib, json, uuid, pathlib, glob, datetime, os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
import httpx

from .db import get_db
from .models import Engagement, Plan, Run
from .auth import get_principal, Principal
from .tenancy import set_tenant_guc, require_tenant, ensure_membership

APP_ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_DIR = APP_ROOT / "catalog" / "tests"
OPA_URL = os.environ.get("OPA_URL","http://localhost:8181/v1/data/pentest/policy")

app = FastAPI(title="AI Testing Orchestrator (v2)", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Models (requests) -----

class Scope(BaseModel):
    in_scope_domains: List[str] = Field(default_factory=list)
    in_scope_cidrs: List[str] = Field(default_factory=list)
    out_of_scope: List[str] = Field(default_factory=list)
    risk_tier: str = Field(default="safe_active")
    windows: List[Dict[str, str]] = Field(default_factory=list)

class EngagementCreate(BaseModel):
    name: str
    tenant_id: str
    type: str
    scope: Scope

class EngagementOut(EngagementCreate):
    id: str

class SelectedTest(BaseModel):
    id: str
    params: Dict[str, Any] = Field(default_factory=dict)

class PlanRequest(BaseModel):
    selected_tests: List[SelectedTest]
    agents: Dict[str, Any] = Field(default_factory=dict)
    risk_tier: str = "safe_active"

class PlanOut(BaseModel):
    id: str
    engagement_id: str
    plan_hash: str
    steps: List[Dict[str, Any]]
    catalog_version: str

class StartTestRequest(BaseModel):
    engagement_id: str
    plan_id: str

class RunOut(BaseModel):
    id: str
    engagement_id: str
    plan_id: str
    status: str

# ----- Quotas & Approvals storage (simple ORM-free queries to keep overlay minimal) -----
from sqlalchemy import table, column, text, Integer, String

def month_key(dt=None):
    dt = dt or datetime.datetime.utcnow()
    return dt.strftime("%Y-%m")

def get_quota(db: Session, tenant_id: str) -> Optional[dict]:
    set_tenant_guc(db, tenant_id)
    row = db.execute(text("""
        SELECT monthly_budget, per_plan_cap, month_key
        FROM quotas WHERE tenant_id=:t AND month_key=:m
    """), {"t": tenant_id, "m": month_key()}).mappings().first()
    return dict(row) if row else None

def upsert_quota(db: Session, tenant_id: str, monthly_budget: int, per_plan_cap: int):
    set_tenant_guc(db, tenant_id)
    mk = month_key()
    exists = db.execute(text("SELECT id FROM quotas WHERE tenant_id=:t AND month_key=:m"),
                        {"t": tenant_id, "m": mk}).scalar()
    if exists:
        db.execute(text("UPDATE quotas SET monthly_budget=:b, per_plan_cap=:p WHERE tenant_id=:t AND month_key=:m"),
                   {"b": monthly_budget, "p": per_plan_cap, "t": tenant_id, "m": mk})
    else:
        db.execute(text("INSERT INTO quotas (id, tenant_id, monthly_budget, per_plan_cap, month_key) VALUES (:id,:t,:b,:p,:m)"),
                   {"id": f"q_{uuid.uuid4().hex[:10]}", "t": tenant_id, "b": monthly_budget, "p": per_plan_cap, "m": mk})
    db.commit()
    return get_quota(db, tenant_id)

def sum_usage(db: Session, tenant_id: str) -> int:
    set_tenant_guc(db, tenant_id)
    mk = month_key()
    val = db.execute(text("SELECT COALESCE(SUM(credits),0) FROM quota_usage WHERE tenant_id=:t AND month_key=:m"),
                     {"t": tenant_id, "m": mk}).scalar()
    return int(val or 0)

def accrue_usage(db: Session, tenant_id: str, engagement_id: str, run_id: str, credits: int):
    set_tenant_guc(db, tenant_id)
    db.execute(text("INSERT INTO quota_usage (id, tenant_id, run_id, engagement_id, credits, month_key) VALUES (:id,:t,:r,:e,:c,:m)"),
               {"id": f"u_{uuid.uuid4().hex[:10]}", "t": tenant_id, "r": run_id, "e": engagement_id, "c": credits, "m": month_key()})
    db.commit()

def approval_status(db: Session, tenant_id: str, engagement_id: str) -> str:
    set_tenant_guc(db, tenant_id)
    st = db.execute(text("SELECT status FROM approvals WHERE tenant_id=:t AND engagement_id=:e ORDER BY created_at DESC LIMIT 1"),
                    {"t": tenant_id, "e": engagement_id}).scalar()
    return st or "none"

def request_approval(db: Session, tenant_id: str, engagement_id: str, reason: str, creator_user_id: str) -> dict:
    set_tenant_guc(db, tenant_id)
    aid = f"ap_{uuid.uuid4().hex[:10]}"
    db.execute(text("INSERT INTO approvals (id, tenant_id, engagement_id, status, reason, created_by) VALUES (:id,:t,:e,'pending',:r,:u)"),
               {"id": aid, "t": tenant_id, "e": engagement_id, "r": reason, "u": creator_user_id})
    db.commit()
    return {"id": aid, "status": "pending"}

def decide_approval(db: Session, tenant_id: str, approval_id: str, decision: str, decider_user_id: str):
    if decision not in ("approved","denied"):
        raise HTTPException(status_code=400, detail="invalid decision")
    set_tenant_guc(db, tenant_id)
    db.execute(text("UPDATE approvals SET status=:s, decided_by=:u, decided_at=now() WHERE id=:id AND tenant_id=:t"),
               {"s": decision, "u": decider_user_id, "id": approval_id, "t": tenant_id})
    db.commit()

# ----- Catalog helpers -----

def load_catalog() -> Dict[str, Any]:
    items = []
    for path in glob.glob(str(CATALOG_DIR / "*.json")):
        with open(path, "r") as f:
            items.append(json.load(f))
    return {"version": "0.1.0", "items": items}

def catalog_index(catalog):
    return {i["id"]: i for i in catalog["items"]}

def estimate_cost_and_duration(selected_tests: List[SelectedTest], idx: Dict[str, Any], asset_counts: Dict[str,int] | None=None):
    total_cost = 0
    total_sec = 0
    for t in selected_tests:
        item = idx.get(t.id, {})
        est = item.get("estimator", {})
        tph = est.get("time_per_host_sec", 0)
        cu = est.get("cost_units", 0)
        # naive: multiply by hosts=asset_counts.get("hosts",1) if present
        hosts = (asset_counts or {}).get("hosts", 1)
        total_sec += int(tph) * max(1, hosts)
        total_cost += int(cu) * max(1, hosts)
    return {"duration_sec": total_sec, "cost_units": total_cost}

def requires_intrusive(selected_tests: List[SelectedTest], idx: Dict[str,Any]) -> bool:
    for t in selected_tests:
        if idx.get(t.id,{}).get("risk_tier") == "intrusive":
            return True
    return False

async def opa_check(input_payload: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(OPA_URL, json={"input": input_payload})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        return {"error": str(e)}

# ----- Routes -----

@app.get("/health")
def health():
    return {"ok": True, "version": app.version}

@app.get("/v1/catalog")
def get_catalog(_: Principal = Depends(require_tenant)):
    return load_catalog()

@app.get("/v1/catalog/packs")
def get_packs(_: Principal = Depends(require_tenant)):
    # Minimal packs example; front-end can render as checkboxes
    return {
        "packs": [
            {"id":"pack.standard_network","name":"Standard Network","tests":["network.discovery.ping_sweep","network.nmap.tcp_top_1000"]},
            {"id":"pack.web_owasp_core","name":"Web OWASP Core","tests":["web.owasp.top10.core"]}
        ]
    }

@app.post("/v1/engagements", response_model=EngagementOut)
def create_engagement(body: EngagementCreate, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    ensure_membership(db, principal, body.tenant_id)
    set_tenant_guc(db, body.tenant_id)
    eid = f"eng_{uuid.uuid4().hex[:12]}"
    e = Engagement(id=eid, tenant_id=body.tenant_id, name=body.name, type=body.type, scope=body.scope.model_dump())
    db.add(e); db.commit()
    return EngagementOut(id=e.id, tenant_id=e.tenant_id, name=e.name, type=e.type, scope=e.scope)

@app.post("/v2/engagements/{engagement_id}/plan/validate")
async def plan_validate(engagement_id: str, body: PlanRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(select(Engagement).where(Engagement.id == engagement_id)).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="engagement not found")
    ensure_membership(db, principal, e.tenant_id)
    set_tenant_guc(db, e.tenant_id)

    catalog = load_catalog()
    idx = catalog_index(catalog)

    errors = []
    selected_ids = [t.id for t in body.selected_tests]
    for t in body.selected_tests:
        if t.id not in idx:
            errors.append({"test_id": t.id, "reason": "unknown test id"})
    for t in body.selected_tests:
        item = idx.get(t.id); 
        if not item: continue
        for pre in item.get("prerequisites", []):
            if pre not in selected_ids:
                errors.append({"test_id": t.id, "reason": f"missing prerequisite: {pre}"})
        for c in item.get("exclusive_with", []):
            if c in selected_ids:
                errors.append({"test_id": t.id, "reason": f"conflicts with: {c}"})

    est = estimate_cost_and_duration(body.selected_tests, idx, asset_counts={"hosts": 1})
    quota = get_quota(db, e.tenant_id)
    used = sum_usage(db, e.tenant_id)
    over_quota = False
    over_reason = None
    if quota:
        if est["cost_units"] > quota["per_plan_cap"]:
            over_quota = True; over_reason = "per_plan_cap"
        if used + est["cost_units"] > quota["monthly_budget"]:
            over_quota = True; over_reason = (over_reason or "monthly_budget")

    # OPA check
    approval_granted = (approval_status(db, e.tenant_id, engagement_id) == "approved")
    opa_input = {"risk_tier": body.risk_tier, "scope": e.scope, "approval_granted": approval_granted}
    opa_res = await opa_check(opa_input)
    opa_denies = opa_res.get("result",{}).get("deny",[])

    ok = (len(errors) == 0) and (not over_quota) and (not opa_denies)
    return {
        "ok": ok,
        "errors": errors,
        "estimate": est,
        "quota": {"configured": bool(quota), "used": used, "monthly_budget": quota["monthly_budget"] if quota else None, "per_plan_cap": quota["per_plan_cap"] if quota else None, "status": "over_quota" if over_quota else "ok", "reason": over_reason},
        "opa": {"deny": opa_denies, "raw": opa_res}
    }

@app.post("/v2/engagements/{engagement_id}/plan/preview")
def plan_preview(engagement_id: str, body: PlanRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(select(Engagement).where(Engagement.id == engagement_id)).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="engagement not found")
    ensure_membership(db, principal, e.tenant_id)
    set_tenant_guc(db, e.tenant_id)

    catalog = load_catalog()
    idx = catalog_index(catalog)

    ordered = sorted(body.selected_tests, key=lambda t: (idx.get(t.id,{}).get("category","zzz"), t.id))
    steps = []
    for t in ordered:
        item = idx.get(t.id,{})
        steps.append({
            "test_id": t.id,
            "tool_adapter": item.get("tool_adapter"),
            "risk_tier": item.get("risk_tier"),
            "params": t.params,
            "agent_constraints": item.get("requires", {}).get("agents", []),
            "outputs": item.get("outputs", []),
        })
    return {"steps": steps}

@app.post("/v1/engagements/{engagement_id}/plan", response_model=PlanOut)
def create_plan(engagement_id: str, body: PlanRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(select(Engagement).where(Engagement.id == engagement_id)).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="engagement not found")
    ensure_membership(db, principal, e.tenant_id)
    set_tenant_guc(db, e.tenant_id)

    # Check quotas & OPA again (defensive)
    catalog = load_catalog()
    idx = catalog_index(catalog)
    est = estimate_cost_and_duration(body.selected_tests, idx, asset_counts={"hosts": 1})
    quota = get_quota(db, e.tenant_id)
    used = sum_usage(db, e.tenant_id)
    if quota:
        if est["cost_units"] > quota["per_plan_cap"] or used + est["cost_units"] > quota["monthly_budget"]:
            raise HTTPException(status_code=402, detail={"reason":"over_quota","estimate":est,"quota":{"used":used, "monthly_budget": quota["monthly_budget"], "per_plan_cap": quota["per_plan_cap"]}})

    # OPA deny?
    approval_granted = (approval_status(db, e.tenant_id, engagement_id) == "approved")
    opa_input = {"risk_tier": body.risk_tier, "scope": e.scope, "approval_granted": approval_granted}
    # Best-effort sync call
    try:
        import requests
        r = requests.post(OPA_URL, json={"input": opa_input}, timeout=3)
        r.raise_for_status()
        denies = r.json().get("result",{}).get("deny",[])
        if denies:
            raise HTTPException(status_code=403, detail={"reason":"policy_denied","messages":denies})
    except Exception:
        pass  # allow if OPA unavailable; rely on agent-side guardrails later

    # Build steps deterministically
    selected_ids = [t.id for t in body.selected_tests]
    errors = []
    for t in body.selected_tests:
        if t.id not in idx:
            errors.append({"test_id": t.id, "reason":"unknown test id"})
    for t in body.selected_tests:
        item = idx.get(t.id); 
        if not item: continue
        for pre in item.get("prerequisites", []):
            if pre not in selected_ids:
                errors.append({"test_id": t.id, "reason": f"missing prerequisite: {pre}"})
        for c in item.get("exclusive_with", []):
            if c in selected_ids:
                errors.append({"test_id": t.id, "reason": f"conflicts with: {c}"})
    if errors:
        raise HTTPException(status_code=422, detail={"validation": errors})

    ordered = sorted(body.selected_tests, key=lambda t: (idx[t.id].get("category","zzz"), t.id))
    steps = []
    for t in ordered:
        item = idx[t.id]
        steps.append({
            "id": f"step_{uuid.uuid4().hex[:8]}",
            "test_id": t.id,
            "tool_adapter": item.get("tool_adapter"),
            "risk_tier": item.get("risk_tier"),
            "params": t.params,
            "agent_constraints": item.get("requires", {}).get("agents", []),
            "outputs": item.get("outputs", []),
        })
    plan_raw = {"engagement_id": engagement_id, "steps": steps, "catalog_version": "0.1.0"}
    plan_hash = hashlib.sha256(json.dumps(plan_raw, sort_keys=True).encode()).hexdigest()
    pid = f"plan_{uuid.uuid4().hex[:12]}"
    from .models import Plan as PlanModel
    p = PlanModel(id=pid, tenant_id=e.tenant_id, engagement_id=engagement_id, plan_hash=plan_hash, data=plan_raw, catalog_version="0.1.0")
    db.add(p); db.commit()
    return PlanOut(id=p.id, engagement_id=p.engagement_id, plan_hash=p.plan_hash, steps=steps, catalog_version=p.catalog_version)

@app.post("/v1/tests", response_model=RunOut)
def start_test(body: StartTestRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(select(Engagement).where(Engagement.id == body.engagement_id)).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="engagement not found")
    ensure_membership(db, principal, e.tenant_id)
    set_tenant_guc(db, e.tenant_id)
    p = db.execute(select(Plan).where(Plan.id == body.plan_id, Plan.engagement_id == body.engagement_id)).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="plan not found for engagement")

    # Quota re-check and approval gating
    catalog = load_catalog()
    idx = catalog_index(catalog)
    selected_tests = [SelectedTest(id=s["test_id"], params=s.get("params",{})) for s in p.data.get("steps",[])]
    est = estimate_cost_and_duration(selected_tests, idx, asset_counts={"hosts":1})
    quota = get_quota(db, e.tenant_id)
    used = sum_usage(db, e.tenant_id)
    if quota and (used + est["cost_units"] > quota["monthly_budget"]):
        raise HTTPException(status_code=402, detail={"reason":"over_quota_at_start","estimate":est,"used":used,"budget":quota["monthly_budget"]})

    if requires_intrusive(selected_tests, idx):
        if approval_status(db, e.tenant_id, body.engagement_id) != "approved":
            raise HTTPException(status_code=403, detail={"reason":"approval_required"})

    rid = f"run_{uuid.uuid4().hex[:12]}"
    r = Run(id=rid, tenant_id=e.tenant_id, engagement_id=e.id, plan_id=p.id, status="running")
    db.add(r); db.commit()

    # accrue usage immediately (simple; refine later with phase-based accrual)
    if quota:
        accrue_usage(db, e.tenant_id, e.id, r.id, est["cost_units"])

    return RunOut(id=r.id, engagement_id=r.engagement_id, plan_id=r.plan_id, status=r.status)

# ---- Quotas API ----
class QuotaIn(BaseModel):
    tenant_id: str
    monthly_budget: int
    per_plan_cap: int

@app.post("/v2/quotas")
def set_quota(body: QuotaIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    ensure_membership(db, principal, body.tenant_id)
    q = upsert_quota(db, body.tenant_id, body.monthly_budget, body.per_plan_cap)
    return q

@app.get("/v2/quotas/{tenant_id}")
def get_quota_api(tenant_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    ensure_membership(db, principal, tenant_id)
    q = get_quota(db, tenant_id)
    used = sum_usage(db, tenant_id)
    return {"quota": q, "used": used}

# ---- Approvals API ----
class ApprovalIn(BaseModel):
    tenant_id: str
    engagement_id: str
    reason: str

class ApprovalDecision(BaseModel):
    tenant_id: str
    decision: str  # approved | denied

@app.post("/v2/approvals")
def approvals_request(body: ApprovalIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    ensure_membership(db, principal, body.tenant_id)
    res = request_approval(db, body.tenant_id, body.engagement_id, body.reason, principal.user_id)
    return res

@app.post("/v2/approvals/{approval_id}/decide")
def approvals_decide(approval_id: str, body: ApprovalDecision, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    ensure_membership(db, principal, body.tenant_id)
    decide_approval(db, body.tenant_id, approval_id, body.decision, principal.user_id)
    return {"id": approval_id, "status": body.decision}
