import hashlib, json, uuid, pathlib, glob, datetime, os, asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, text
import httpx, requests
from sse_starlette.sse import EventSourceResponse

from .db import get_db, SessionLocal
from .models import Engagement, Plan, Run
from .auth import get_principal, Principal
from .tenancy import set_tenant_guc, require_tenant, ensure_membership

APP_ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_DIR = APP_ROOT / "catalog" / "tests"
OPA_URL = os.environ.get("OPA_URL","http://localhost:8181/v1/data/pentest/policy")
SIMULATE = os.environ.get("SIMULATE_PROGRESS","false").lower() == "true"
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")

app = FastAPI(title="AI Testing Orchestrator (v2)", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- Models ---------

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

# --------- Quota/Approval helpers (reused) ---------
def month_key(dt=None):
    dt = dt or datetime.datetime.utcnow()
    return dt.strftime("%Y-%m")

def get_quota(db: Session, tenant_id: str) -> Optional[dict]:
    set_tenant_guc(db, tenant_id)
    row = db.execute(text("SELECT monthly_budget, per_plan_cap, month_key FROM quotas WHERE tenant_id=:t AND month_key=:m"),
                     {"t": tenant_id, "m": month_key()}).mappings().first()
    return dict(row) if row else None

def sum_usage(db: Session, tenant_id: str) -> int:
    set_tenant_guc(db, tenant_id)
    val = db.execute(text("SELECT COALESCE(SUM(credits),0) FROM quota_usage WHERE tenant_id=:t AND month_key=:m"),
                     {"t": tenant_id, "m": month_key()}).scalar()
    return int(val or 0)

def approval_status(db: Session, tenant_id: str, engagement_id: str) -> str:
    set_tenant_guc(db, tenant_id)
    st = db.execute(text("SELECT status FROM approvals WHERE tenant_id=:t AND engagement_id=:e ORDER BY created_at DESC LIMIT 1"),
                    {"t": tenant_id, "e": engagement_id}).scalar()
    return st or "none"

def accrue_usage(db: Session, tenant_id: str, engagement_id: str, run_id: str, credits: int):
    set_tenant_guc(db, tenant_id)
    db.execute(text("INSERT INTO quota_usage (id, tenant_id, run_id, engagement_id, credits, month_key) VALUES (:id,:t,:r,:e,:c,:m)"),
               {"id": f"u_{uuid.uuid4().hex[:10]}", "t": tenant_id, "r": run_id, "e": engagement_id, "c": credits, "m": month_key()})
    db.commit()

# --------- Catalog helpers ---------
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
        hosts = (asset_counts or {}).get("hosts", 1)
        total_sec += int(tph) * max(1, hosts)
        total_cost += int(cu) * max(1, hosts)
    return {"duration_sec": total_sec, "cost_units": total_cost}

def requires_intrusive(selected_tests: List[SelectedTest], idx: Dict[str,Any]) -> bool:
    for t in selected_tests:
        if idx.get(t.id,{}).get("risk_tier") == "intrusive":
            return True
    return False

# --------- OPA ---------
async def opa_check(input_payload: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(OPA_URL, json={"input": input_payload})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        return {"error": str(e)}

# --------- Event helpers ---------
def insert_event(db: Session, tenant_id: str, run_id: str, ev_type: str, payload: dict):
    set_tenant_guc(db, tenant_id)
    db.execute(text("INSERT INTO run_events (id, tenant_id, run_id, type, payload) VALUES (:id,:t,:r,:ty,:pl)"),
               {"id": f"ev_{uuid.uuid4().hex[:12]}", "t": tenant_id, "r": run_id, "ty": ev_type, "pl": json.dumps(payload)})
    db.commit()

async def simulate_progress(run_id: str, tenant_id: str, steps: list):
    # Run in background; poll run status to honor pause/abort
    try:
        i = 0
        with SessionLocal() as s:
            set_tenant_guc(s, tenant_id)
            insert_event(s, tenant_id, run_id, "run.started", {"message":"Run started"})
        for step in steps:
            while True:
                await asyncio.sleep(0.5)
                with SessionLocal() as s:
                    set_tenant_guc(s, tenant_id)
                    status = s.execute(text("SELECT status FROM runs WHERE id=:r"), {"r": run_id}).scalar()
                    if status == "aborted":
                        insert_event(s, tenant_id, run_id, "run.aborted", {"message":"Run aborted"})
                        return
                    if status == "paused":
                        continue
                    break
            with SessionLocal() as s:
                set_tenant_guc(s, tenant_id)
                insert_event(s, tenant_id, run_id, "step.started", {"test_id": step.get("test_id")})
            await asyncio.sleep(1.2)
            with SessionLocal() as s:
                set_tenant_guc(s, tenant_id)
                insert_event(s, tenant_id, run_id, "step.completed", {"test_id": step.get("test_id"), "result":"ok"})
            i += 1
        with SessionLocal() as s:
            set_tenant_guc(s, tenant_id)
            s.execute(text("UPDATE runs SET status='completed' WHERE id=:r"), {"r": run_id})
            s.commit()
            insert_event(s, tenant_id, run_id, "run.completed", {"message":"Run completed"})
            if SLACK_WEBHOOK:
                try:
                    requests.post(SLACK_WEBHOOK, json={"text": f":white_check_mark: Run {run_id} completed"} , timeout=3)
                except Exception:
                    pass
    except Exception:
        with SessionLocal() as s:
            set_tenant_guc(s, tenant_id)
            s.execute(text("UPDATE runs SET status='failed' WHERE id=:r"), {"r": run_id}); s.commit()
            insert_event(s, tenant_id, run_id, "run.failed", {"message":"Run failed unexpectedly"})

# --------- Routes ---------

@app.get("/health")
def health():
    return {"ok": True, "version": app.version}

@app.get("/v1/catalog")
def get_catalog(_: Principal = Depends(require_tenant)):
    return load_catalog()

@app.get("/v1/catalog/packs")
def get_packs(_: Principal = Depends(require_tenant)):
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

# ---- Validate / Preview (as in Batch 3) ----
class PlanValidateRequest(PlanRequest): pass

@app.post("/v2/engagements/{engagement_id}/plan/validate")
async def plan_validate(engagement_id: str, body: PlanValidateRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
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
    over_quota = False; reason = None
    if quota:
        if est["cost_units"] > quota["per_plan_cap"]:
            over_quota = True; reason = "per_plan_cap"
        if used + est["cost_units"] > quota["monthly_budget"]:
            over_quota = True; reason = (reason or "monthly_budget")

    approval_granted = (approval_status(db, e.tenant_id, engagement_id) == "approved")
    opa_input = {"risk_tier": body.risk_tier, "scope": e.scope, "approval_granted": approval_granted}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(OPA_URL, json={"input": opa_input}); r.raise_for_status()
            opa_res = r.json()
    except Exception as ex:
        opa_res = {"error": str(ex)}
    denies = opa_res.get("result",{}).get("deny",[])

    ok = (len(errors) == 0) and (not over_quota) and (not denies)
    return {"ok": ok, "errors": errors, "estimate": est,
            "quota": {"configured": bool(quota), "used": used, "status": "over_quota" if over_quota else "ok", "reason": reason, **(quota or {})},
            "opa": {"deny": denies}}

@app.post("/v2/engagements/{engagement_id}/plan/preview")
def plan_preview(engagement_id: str, body: PlanRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(select(Engagement).where(Engagement.id == engagement_id)).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="engagement not found")
    ensure_membership(db, principal, e.tenant_id); set_tenant_guc(db, e.tenant_id)
    catalog = load_catalog(); idx = catalog_index(catalog)
    ordered = sorted(body.selected_tests, key=lambda t: (idx.get(t.id,{}).get("category","zzz"), t.id))
    steps = [{
        "test_id": t.id,
        "tool_adapter": idx.get(t.id,{}).get("tool_adapter"),
        "risk_tier": idx.get(t.id,{}).get("risk_tier"),
        "params": t.params,
        "agent_constraints": idx.get(t.id,{}).get("requires",{}).get("agents",[]),
        "outputs": idx.get(t.id,{}).get("outputs",[])
    } for t in ordered]
    return {"steps": steps}

# ---- Plan creation (unchanged guardrails; minimal) ----
@app.post("/v1/engagements/{engagement_id}/plan", response_model=PlanOut)
def create_plan(engagement_id: str, body: PlanRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(select(Engagement).where(Engagement.id == engagement_id)).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="engagement not found")
    ensure_membership(db, principal, e.tenant_id); set_tenant_guc(db, e.tenant_id)

    catalog = load_catalog(); idx = catalog_index(catalog)
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

# ---- Start test + simulation ----
@app.post("/v1/tests", response_model=RunOut)
def start_test(body: StartTestRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(select(Engagement).where(Engagement.id == body.engagement_id)).scalar_one_or_none()
    if not e: raise HTTPException(status_code=404, detail="engagement not found")
    ensure_membership(db, principal, e.tenant_id); set_tenant_guc(db, e.tenant_id)
    p = db.execute(select(Plan).where(Plan.id == body.plan_id, Plan.engagement_id == body.engagement_id)).scalar_one_or_none()
    if not p: raise HTTPException(status_code=404, detail="plan not found for engagement")

    rid = f"run_{uuid.uuid4().hex[:12]}"
    r = Run(id=rid, tenant_id=e.tenant_id, engagement_id=e.id, plan_id=p.id, status="running")
    db.add(r); db.commit()

    # initial events
    insert_event(db, e.tenant_id, r.id, "run.queued", {"message":"Run queued"})
    steps = [{"test_id": s["test_id"], "params": s.get("params",{})} for s in p.data.get("steps",[])]

    # notify Slack
    if SLACK_WEBHOOK:
        try:
            requests.post(SLACK_WEBHOOK, json={"text": f":rocket: Run {r.id} started for engagement {e.id}"}, timeout=3)
        except Exception:
            pass

    # simulate if enabled
    if SIMULATE and steps:
        asyncio.get_event_loop().create_task(simulate_progress(r.id, e.tenant_id, steps))
    return RunOut(id=r.id, engagement_id=r.engagement_id, plan_id=r.plan_id, status=r.status)

@app.get("/v1/tests/{run_id}", response_model=RunOut)
def get_run(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(select(Run).where(Run.id == run_id)).scalar_one_or_none()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r.tenant_id)
    return RunOut(id=r.id, engagement_id=r.engagement_id, plan_id=r.plan_id, status=r.status)

# ---- SSE stream ----
@app.get("/v2/runs/{run_id}/events")
def events_stream(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(select(Run).where(Run.id == run_id)).scalar_one_or_none()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r.tenant_id)

    async def gen(last_seen: Optional[str] = None):
        last_ts = None
        while True:
            await asyncio.sleep(0.6)
            with SessionLocal() as s:
                set_tenant_guc(s, r.tenant_id)
                if last_ts is None:
                    rows = s.execute(text("SELECT id,type,payload,created_at FROM run_events WHERE run_id=:rid ORDER BY created_at ASC LIMIT 50"),
                                     {"rid": run_id}).mappings().all()
                else:
                    rows = s.execute(text("SELECT id,type,payload,created_at FROM run_events WHERE run_id=:rid AND created_at > :ts ORDER BY created_at ASC LIMIT 50"),
                                     {"rid": run_id, "ts": last_ts}).mappings().all()
            for row in rows:
                last_ts = row["created_at"]
                yield {"event": row["type"], "id": row["id"], "data": json.dumps(row["payload"])}
            # keepalive
            yield {"event":"keepalive", "data":"{}"}

    return EventSourceResponse(gen())

# ---- Run controls ----
class ControlIn(BaseModel):
    action: str  # pause|resume|abort

@app.post("/v2/runs/{run_id}/control")
def run_control(run_id: str, body: ControlIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(select(Run).where(Run.id == run_id)).scalar_one_or_none()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r.tenant_id)

    if body.action not in ("pause","resume","abort"):
        raise HTTPException(status_code=400, detail="invalid action")

    if body.action == "pause":
        db.execute(text("UPDATE runs SET status='paused' WHERE id=:r"), {"r": run_id}); db.commit()
        insert_event(db, r.tenant_id, run_id, "run.paused", {"by":"user"})
        return {"ok": True, "status": "paused"}
    if body.action == "resume":
        db.execute(text("UPDATE runs SET status='running' WHERE id=:r"), {"r": run_id}); db.commit()
        insert_event(db, r.tenant_id, run_id, "run.resumed", {"by":"user"})
        return {"ok": True, "status": "running"}
    if body.action == "abort":
        db.execute(text("UPDATE runs SET status='aborted' WHERE id=:r"), {"r": run_id}); db.commit()
        insert_event(db, r.tenant_id, run_id, "run.aborted", {"by":"user"})
        if SLACK_WEBHOOK:
            try:
                requests.post(SLACK_WEBHOOK, json={"text": f":stop_sign: Run {run_id} aborted"}, timeout=3)
            except Exception:
                pass
        return {"ok": True, "status": "aborted"}
