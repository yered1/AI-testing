import hashlib, json, uuid, pathlib, glob, ipaddress, urllib.parse, math
from typing import List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import get_db
from .models import Engagement, Plan, Run
from .auth import get_principal, Principal
from .tenancy import set_tenant_guc, require_tenant, ensure_membership

APP_ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_DIR = APP_ROOT / "catalog" / "tests"

app = FastAPI(title="AI Testing Orchestrator (v2)", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def load_catalog() -> Dict[str, Any]:
    items = []
    for path in glob.glob(str(CATALOG_DIR / "*.json")):
        with open(path, "r") as f:
            items.append(json.load(f))
    return {"version": "0.2.0", "items": items}

def catalog_index(catalog):
    return {i["id"]: i for i in catalog["items"]}

@app.get("/health")
def health():
    return {"ok": True, "version": app.version}

@app.get("/v1/catalog")
def get_catalog(_: Principal = Depends(require_tenant)):
    return load_catalog()

@app.get("/v1/catalog/packs")
def get_catalog_packs(_: Principal = Depends(require_tenant)):
    packs_dir = APP_ROOT / "catalog" / "packs"
    packs = []
    for path in glob.glob(str(packs_dir / "*.json")):
        with open(path, "r") as f:
            packs.append(json.load(f))
    return {"items": packs}

@app.post("/v1/engagements", response_model=EngagementOut)
def create_engagement(body: EngagementCreate, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    ensure_membership(db, principal, body.tenant_id)
    set_tenant_guc(db, body.tenant_id)
    eid = f"eng_{uuid.uuid4().hex[:12]}"
    e = Engagement(id=eid, tenant_id=body.tenant_id, name=body.name, type=body.type, scope=body.scope.model_dump())
    db.add(e); db.commit()
    return EngagementOut(id=e.id, tenant_id=e.tenant_id, name=e.name, type=e.type, scope=e.scope)

@app.post("/v1/engagements/{engagement_id}/plan", response_model=PlanOut)
def create_plan(engagement_id: str, body: PlanRequest, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(select(Engagement).where(Engagement.id == engagement_id)).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="engagement not found")
    ensure_membership(db, principal, e.tenant_id)
    set_tenant_guc(db, e.tenant_id)

    catalog = load_catalog()
    idx = catalog_index(catalog)

    # validate
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
    plan_raw = {"engagement_id": engagement_id, "steps": steps, "catalog_version": catalog["version"]}
    plan_hash = hashlib.sha256(json.dumps(plan_raw, sort_keys=True).encode()).hexdigest()
    pid = f"plan_{uuid.uuid4().hex[:12]}"
    p = Plan(id=pid, tenant_id=e.tenant_id, engagement_id=engagement_id, plan_hash=plan_hash, data=plan_raw, catalog_version=catalog["version"])
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
    rid = f"run_{uuid.uuid4().hex[:12]}"
    r = Run(id=rid, tenant_id=e.tenant_id, engagement_id=e.id, plan_id=p.id, status="running")
    db.add(r); db.commit()
    return RunOut(id=r.id, engagement_id=r.engagement_id, plan_id=r.plan_id, status=r.status)

@app.get("/v1/tests/{run_id}", response_model=RunOut)
def get_run(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(select(Run).where(Run.id == run_id)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="run not found")
    set_tenant_guc(db, r.tenant_id)
    return RunOut(id=r.id, engagement_id=r.engagement_id, plan_id=r.plan_id, status=r.status)

# ---------------- Batch 2 logic ----------------

def _count_hosts(scope: dict) -> int:
    total = 0
    for cidr in scope.get("in_scope_cidrs", []):
        try:
            net = ipaddress.ip_network(cidr, strict=False)
            total += max(0, net.num_addresses - (2 if isinstance(net, ipaddress.IPv4Network) and net.prefixlen < 31 else 0))
        except Exception:
            continue
    return min(total, 4096) if total else 1

def _count_web_targets(scope: dict, selected_tests: list) -> int:
    urls = set()
    for t in selected_tests:
        params = t.get("params", {})
        for key in ("url","base_url","target_url"):
            if key in params:
                try:
                    urls.add(urllib.parse.urlparse(params[key]).netloc)
                except Exception:
                    pass
    if not urls:
        for d in scope.get("in_scope_domains", []):
            urls.add(d)
    return min(len(urls), 64) or 1

def _validate_required_inputs(test_item: dict, params: dict) -> list[str]:
    errors = []
    reqs = test_item.get("requires", {}).get("inputs", [])
    for req in reqs:
        alts = [k.strip() for k in req.split("|")]
        if not any(k in params for k in alts):
            errors.append(f"missing required input: {req}")
    return errors

def _estimate(catalog: dict, scope: dict, selected: list[dict]) -> dict:
    idx = {i["id"]: i for i in catalog["items"]}
    host_count = _count_hosts(scope)
    web_count = _count_web_targets(scope, selected)

    total_sec = 0.0
    total_cost = 0.0
    per_test = []

    for t in selected:
        item = idx.get(t["id"])
        if not item: 
            continue
        est = item.get("estimator", {})
        tph = float(est.get("time_per_host_sec", 0))
        cu = float(est.get("cost_units", 0))

        cat = item.get("category")
        if cat == "Network":
            mult = host_count
        elif cat in ("Web","API"):
            mult = web_count
        else:
            mult = 1

        sec = tph * mult
        cost = cu * mult
        total_sec += sec
        total_cost += cost
        per_test.append({"id": t["id"], "assets": int(mult), "seconds": int(sec), "cost_units": int(cost)})

    return {
        "assets": {"network_hosts": host_count, "web_targets": web_count},
        "per_test": per_test,
        "duration_min": int(math.ceil(total_sec / 60.0)),
        "cost_units": int(math.ceil(total_cost))
    }

@app.post("/v2/engagements/{engagement_id}/plan/validate")
def validate_plan(engagement_id: str, body: PlanRequest = Body(...), db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(select(Engagement).where(Engagement.id == engagement_id)).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="engagement not found")
    ensure_membership(db, principal, e.tenant_id)
    set_tenant_guc(db, e.tenant_id)

    catalog = load_catalog()
    idx = catalog_index(catalog)

    selected_ids = [t.id for t in body.selected_tests]
    errors = []
    warnings = []
    suggestions = []

    for t in body.selected_tests:
        if t.id not in idx:
            errors.append({"test_id": t.id, "reason": "unknown test id"})
    for t in body.selected_tests:
        item = idx.get(t.id); 
        if not item: 
            continue
        for pre in item.get("prerequisites", []):
            if pre not in selected_ids:
                errors.append({"test_id": t.id, "reason": f"missing prerequisite: {pre}"})
        for c in item.get("exclusive_with", []):
            if c in selected_ids:
                errors.append({"test_id": t.id, "reason": f"conflicts with: {c}"})
        req_input_errs = _validate_required_inputs(item, t.params)
        for msg in req_input_errs:
            errors.append({"test_id": t.id, "reason": msg})
        url = t.params.get("url") or t.params.get("base_url")
        if url and e.scope.get("in_scope_domains"):
            try:
                host = urllib.parse.urlparse(url).netloc
                if not any(host.endswith(d) for d in e.scope["in_scope_domains"]):
                    warnings.append({"test_id": t.id, "reason": "url host not matched to in_scope_domains"})
            except Exception:
                warnings.append({"test_id": t.id, "reason": "url not parseable"})

    estimate = _estimate(catalog, e.scope, [t.model_dump() for t in body.selected_tests])

    ok = len(errors) == 0
    return {"ok": ok, "errors": errors, "warnings": warnings, "suggestions": suggestions, "estimate": estimate}

@app.post("/v2/engagements/{engagement_id}/plan/preview", response_model=PlanOut)
def preview_plan(engagement_id: str, body: PlanRequest = Body(...), db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
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
    plan_raw = {"engagement_id": engagement_id, "steps": steps, "catalog_version": catalog["version"]}
    plan_hash = hashlib.sha256(json.dumps(plan_raw, sort_keys=True).encode()).hexdigest()
    pid = f"plan_{uuid.uuid4().hex[:12]}"
    return PlanOut(id=pid, engagement_id=engagement_id, plan_hash=plan_hash, steps=steps, catalog_version=catalog["version"])
