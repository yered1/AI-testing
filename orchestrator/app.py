import os, glob, json, hashlib, time, uuid, pathlib
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

APP_ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_DIR = APP_ROOT / "catalog" / "tests"

app = FastAPI(title="AI Pentest Orchestrator (Starter)", version="0.1.0")

# --- In-memory stores (replace with DB) ---
ENGAGEMENTS: Dict[str, Dict[str, Any]] = {}
PLANS: Dict[str, Dict[str, Any]] = {}
RUNS: Dict[str, Dict[str, Any]] = {}

# --- Models ---
class Scope(BaseModel):
    in_scope_domains: List[str] = Field(default_factory=list)
    in_scope_cidrs: List[str] = Field(default_factory=list)
    out_of_scope: List[str] = Field(default_factory=list)
    risk_tier: str = Field(default="safe_active")
    windows: List[Dict[str, str]] = Field(default_factory=list)  # [{"start":"...Z","end":"...Z"}]

class EngagementCreate(BaseModel):
    name: str
    tenant_id: str
    type: str  # "network"|"webapp"|"api"|"mobile"|"code"|"cloud"
    scope: Scope

class Engagement(EngagementCreate):
    id: str

class SelectedTest(BaseModel):
    id: str
    params: Dict[str, Any] = Field(default_factory=dict)

class PlanRequest(BaseModel):
    selected_tests: List[SelectedTest]
    agents: Dict[str, Any] = Field(default_factory=dict)
    risk_tier: str = "safe_active"

class Plan(BaseModel):
    id: str
    engagement_id: str
    plan_hash: str
    steps: List[Dict[str, Any]]
    catalog_version: str = "0.1.0"

class StartTestRequest(BaseModel):
    engagement_id: str
    plan_id: str

class Run(BaseModel):
    id: str
    engagement_id: str
    plan_id: str
    status: str = "queued"  # queued | running | completed | failed
    created_at: float = time.time()

# --- Utils ---
def load_catalog() -> Dict[str, Any]:
    items = []
    for path in glob.glob(str(CATALOG_DIR / "*.json")):
        with open(path, "r") as f:
            try:
                item = json.load(f)
                items.append(item)
            except Exception as e:
                print(f"Failed to load catalog item {path}: {e}")
    return {"version": "0.1.0", "items": items}

def catalog_index(catalog):
    return {i["id"]: i for i in catalog["items"]}

# --- Routes ---

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/v1/catalog")
def get_catalog():
    return load_catalog()

@app.post("/v1/engagements", response_model=Engagement)
def create_engagement(body: EngagementCreate):
    eid = f"eng_{uuid.uuid4().hex[:12]}"
    engagement = body.model_dump()
    engagement["id"] = eid
    ENGAGEMENTS[eid] = engagement
    return engagement

@app.post("/v1/engagements/{engagement_id}/plan", response_model=Plan)
def create_plan(engagement_id: str, body: PlanRequest):
    if engagement_id not in ENGAGEMENTS:
        raise HTTPException(status_code=404, detail="engagement not found")
    catalog = load_catalog()
    idx = catalog_index(catalog)

    # Validate selected tests exist and basic conflicts/prereqs
    steps = []
    selected_ids = [t.id for t in body.selected_tests]
    errors = []

    # Check existence
    for t in body.selected_tests:
        if t.id not in idx:
            errors.append({"test_id": t.id, "reason": "unknown test id"})

    # Prereqs & conflicts
    for t in body.selected_tests:
        if t.id not in idx: 
            continue
        item = idx[t.id]
        for pre in item.get("prerequisites", []):
            if pre not in selected_ids:
                errors.append({"test_id": t.id, "reason": f"missing prerequisite: {pre}"})
        for c in item.get("exclusive_with", []):
            if c in selected_ids:
                errors.append({"test_id": t.id, "reason": f"conflicts with: {c}"})

    if errors:
        raise HTTPException(status_code=422, detail={"validation": errors})

    # Build steps deterministically (simple: order by category then id)
    ordered = sorted(body.selected_tests, key=lambda t: (idx[t.id].get("category","zzz"), t.id))
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

    plan_raw = {
        "engagement_id": engagement_id,
        "steps": steps,
        "catalog_version": catalog["version"]
    }
    plan_hash = hashlib.sha256(json.dumps(plan_raw, sort_keys=True).encode()).hexdigest()
    pid = f"plan_{uuid.uuid4().hex[:12]}"
    plan = {
        "id": pid,
        "engagement_id": engagement_id,
        "plan_hash": plan_hash,
        "steps": steps,
        "catalog_version": catalog["version"]
    }
    PLANS[pid] = plan
    return plan

@app.post("/v1/tests", response_model=Run)
def start_test(body: StartTestRequest):
    if body.engagement_id not in ENGAGEMENTS:
        raise HTTPException(status_code=404, detail="engagement not found")
    if body.plan_id not in PLANS:
        raise HTTPException(status_code=404, detail="plan not found")

    rid = f"run_{uuid.uuid4().hex[:12]}"
    run = {"id": rid, "engagement_id": body.engagement_id, "plan_id": body.plan_id, "status": "running", "created_at": time.time()}
    RUNS[rid] = run
    return run

@app.get("/v1/tests/{run_id}", response_model=Run)
def get_run(run_id: str):
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run

# Placeholder SSE (not functional in this skeleton; implement later)
@app.get("/v1/tests/{run_id}/stream")
def stream_run(run_id: str):
    def gen():
        yield "event: keepalive\n"
        yield "data: {\"ok\": true}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")
