import hashlib, json, uuid, pathlib, glob, datetime, os, asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Response, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from sse_starlette.sse import EventSourceResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .db import get_db, SessionLocal
from .models import Engagement, Plan, Run
from .auth import Principal
from .tenancy import set_tenant_guc, require_tenant

APP_ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_DIR = APP_ROOT / "catalog" / "tests"
PACKS_DIR = APP_ROOT / "catalog" / "packs"
TEMPLATE_DIR = pathlib.Path(__file__).resolve().parent / "templates"

OPA_URL = os.environ.get("OPA_URL","http://opa:8181/v1/data/pentest/policy")
SIMULATE = os.environ.get("SIMULATE_PROGRESS","false").lower() == "true"
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")
EVIDENCE_DIR = pathlib.Path(os.environ.get("EVIDENCE_DIR", "/data/evidence"))

env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(enabled_extensions=("html",))
)

app = FastAPI(title="AI Testing Orchestrator (v2)", version="0.8.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def set_tenant(db: Session, tenant_id: str):
    set_tenant_guc(db, tenant_id)

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def load_catalog() -> Dict[str, Any]:
    items = []
    for path in glob.glob(str(CATALOG_DIR / "*.json")):
        with open(path, "r") as f:
            items.append(json.load(f))
    return {"version": "0.1.0", "items": items}

def load_packs() -> List[dict]:
    packs = []
    for path in glob.glob(str(PACKS_DIR / "*.json")):
        with open(path, "r") as f:
            packs.append(json.load(f))
    return packs

def insert_event(db: Session, tenant_id: str, run_id: str, ev_type: str, payload: dict):
    set_tenant(db, tenant_id)
    db.execute(text("INSERT INTO run_events (id, tenant_id, run_id, type, payload) VALUES (:id,:t,:r,:ty,:pl)"),
               {"id": f"ev_{uuid.uuid4().hex[:12]}", "t": tenant_id, "r": run_id, "ty": ev_type, "pl": json.dumps(payload)})
    db.commit()

def month_key(dt=None):
    dt = dt or datetime.datetime.utcnow()
    return dt.strftime("%Y-%m")

def get_quota(db: Session, tenant_id: str) -> Optional[dict]:
    set_tenant(db, tenant_id)
    row = db.execute(text("SELECT tenant_id, monthly_budget, per_plan_cap, month_key FROM quotas WHERE tenant_id=:t AND month_key=:m"),
                     {"t": tenant_id, "m": month_key()}).mappings().first()
    return dict(row) if row else None

def sum_usage(db: Session, tenant_id: str) -> int:
    set_tenant(db, tenant_id)
    val = db.execute(text("SELECT COALESCE(SUM(credits),0) FROM quota_usage WHERE tenant_id=:t AND month_key=:m"),
                     {"t": tenant_id, "m": month_key()}).scalar()
    return int(val or 0)

def accrue_usage(db: Session, tenant_id: str, engagement_id: str, run_id: str, credits: int):
    set_tenant(db, tenant_id)
    db.execute(text("INSERT INTO quota_usage (id, tenant_id, run_id, engagement_id, credits, month_key) VALUES (:id,:t,:r,:e,:c,:m)"),
               {"id": f"u_{uuid.uuid4().hex[:10]}", "t": tenant_id, "r": run_id, "e": engagement_id, "c": credits, "m": month_key()})
    db.commit()

@app.get("/health")
def health():
    return {"ok": True, "ts": now_iso(), "version": app.version}

@app.get("/v1/catalog")
def catalog(principal: Principal = Depends(require_tenant)):
    cat = load_catalog()
    return {"version": cat["version"], "items": cat["items"]}

@app.get("/v1/catalog/packs")
def catalog_packs(principal: Principal = Depends(require_tenant)):
    return {"packs": load_packs()}

class EngagementIn(BaseModel):
    name: str
    tenant_id: str
    type: str
    scope: Dict[str, Any] = Field(default_factory=dict)

@app.post("/v1/engagements")
def create_engagement(body: EngagementIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = Engagement(id=f"eng_{uuid.uuid4().hex[:12]}", tenant_id=body.tenant_id, name=body.name, type=body.type, scope=body.scope)
    db.add(e); db.commit()
    return {"id": e.id, "tenant_id": e.tenant_id, "name": e.name, "type": e.type, "scope": e.scope}

class Selection(BaseModel):
    selected_tests: List[Dict[str, Any]]
    agents: Dict[str, Any] = Field(default_factory=dict)
    risk_tier: str = "safe_active"

@app.post("/v2/engagements/{engagement_id}/plan/validate")
def plan_validate(engagement_id: str, body: Selection, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(text("SELECT id, tenant_id, scope FROM engagements WHERE id=:id"), {"id": engagement_id}).mappings().first()
    if not e: raise HTTPException(status_code=404, detail="engagement not found")
    set_tenant(db, e["tenant_id"])
    credits = 5 * len(body.selected_tests)
    quota = get_quota(db, e["tenant_id"]) or {"monthly_budget": 100, "per_plan_cap": 30}
    usage = sum_usage(db, e["tenant_id"])
    over_month = usage + credits > quota["monthly_budget"]
    over_plan = credits > quota["per_plan_cap"]
    # OPA best-effort
    denies = []
    try:
        import requests
        r = requests.post(OPA_URL, json={"input": {"risk_tier": body.risk_tier, "scope": e["scope"], "approval_granted": False}}, timeout=3)
        r.raise_for_status()
        denies = r.json().get("result",{}).get("deny",[])
    except Exception:
        pass
    return {"estimate_credits": credits, "quota": quota, "usage_this_month": usage, "quota_flags":{"over_month": over_month, "over_plan": over_plan}, "policy_denies": denies}

@app.post("/v1/engagements/{engagement_id}/plan")
def plan_create(engagement_id: str, body: Selection, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(text("SELECT id, tenant_id FROM engagements WHERE id=:id"), {"id": engagement_id}).mappings().first()
    if not e: raise HTTPException(status_code=404, detail="engagement not found")
    set_tenant(db, e["tenant_id"])
    data = {"steps": [{"id": (t.get("id") or t.get("test_id")), "params": t.get("params", {}), "tool_adapter": t.get("tool_adapter")} for t in body.selected_tests]}
    pid = f"plan_{uuid.uuid4().hex[:12]}"
    db.execute(text("INSERT INTO plans (id, tenant_id, engagement_id, plan_hash, data, catalog_version) VALUES (:id,:t,:e,:h,:d,'0.1.0')"),
               {"id": pid, "t": e["tenant_id"], "e": e["id"], "h": hashlib.sha256(json.dumps(data).encode()).hexdigest(), "d": json.dumps(data)})
    db.commit()
    return {"id": pid, "engagement_id": e["id"], "data": data}

class QuotaIn(BaseModel):
    tenant_id: str
    monthly_budget: int = 100
    per_plan_cap: int = 30

@app.post("/v2/quotas")
def set_quota(body: QuotaIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant(db, body.tenant_id)
    db.execute(text("""
        INSERT INTO quotas (tenant_id, month_key, monthly_budget, per_plan_cap)
        VALUES (:t, :m, :mb, :pp)
        ON CONFLICT (tenant_id, month_key) DO UPDATE SET monthly_budget=:mb, per_plan_cap=:pp
    """), {"t": body.tenant_id, "m": month_key(), "mb": body.monthly_budget, "pp": body.per_plan_cap})
    db.commit()
    return {"ok": True}

@app.get("/v2/quotas/{tenant_id}")
def get_quota_endpoint(tenant_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    return get_quota(db, tenant_id) or {"tenant_id": tenant_id, "monthly_budget": 100, "per_plan_cap": 30, "month_key": month_key()}

class ApprovalIn(BaseModel):
    tenant_id: str
    engagement_id: str
    reason: str

@app.post("/v2/approvals")
def request_approval(body: ApprovalIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant(db, body.tenant_id)
    aid = f"ap_{uuid.uuid4().hex[:10]}"
    db.execute(text("INSERT INTO approvals (id, tenant_id, engagement_id, status, reason) VALUES (:id,:t,:e,'pending',:r)"),
               {"id": aid, "t": body.tenant_id, "e": body.engagement_id, "r": body.reason})
    db.commit()
    return {"id": aid, "status": "pending"}

class ApprovalDecision(BaseModel):
    tenant_id: str
    decision: str

@app.post("/v2/approvals/{approval_id}/decide")
def decide_approval(approval_id: str, body: ApprovalDecision, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant(db, body.tenant_id)
    if body.decision not in ("approved","denied"):
        raise HTTPException(status_code=400, detail="invalid decision")
    db.execute(text("UPDATE approvals SET status=:s, decided_at=now() WHERE id=:id"), {"s": body.decision, "id": approval_id})
    db.commit()
    return {"ok": True}

@app.get("/v2/approvals")
def approvals_list(engagement_id: Optional[str] = None, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant(db, principal.tenant_id)
    if engagement_id:
        rows = db.execute(text("""SELECT id, tenant_id, engagement_id, status, reason, created_at, decided_at
                                  FROM approvals WHERE tenant_id=current_setting('app.current_tenant', true)
                                  AND engagement_id=:e ORDER BY created_at DESC LIMIT 50"""), {"e": engagement_id}).mappings().all()
    else:
        rows = db.execute(text("""SELECT id, tenant_id, engagement_id, status, reason, created_at, decided_at
                                  FROM approvals WHERE tenant_id=current_setting('app.current_tenant', true)
                                  ORDER BY created_at DESC LIMIT 100""")).mappings().all()
    return {"approvals": [dict(x) for x in rows]}

class StartTestIn(BaseModel):
    engagement_id: str
    plan_id: str

@app.post("/v1/tests")
def start_test(body: StartTestIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(text("SELECT id, tenant_id FROM engagements WHERE id=:id"), {"id": body.engagement_id}).mappings().first()
    if not e: raise HTTPException(status_code=404, detail="engagement not found")
    set_tenant(db, e["tenant_id"])
    p = db.execute(text("SELECT id, data FROM plans WHERE id=:id AND engagement_id=:e"), {"id": body.plan_id, "e": body.engagement_id}).mappings().first()
    if not p: raise HTTPException(status_code=404, detail="plan not found for engagement")
    rid = f"run_{uuid.uuid4().hex[:12]}"
    db.execute(text("INSERT INTO runs (id, tenant_id, engagement_id, plan_id, status) VALUES (:id,:t,:e,:p,'running')"),
               {"id": rid, "t": e["tenant_id"], "e": e["id"], "p": p["id"]})
    insert_event(db, e["tenant_id"], rid, "run.started", {"plan_id": p["id"]})
    # Create jobs per step (if jobs table exists)
    try:
        steps = (p["data"] or {}).get("steps", [])
        for idx, step in enumerate(steps):
            db.execute(text("""
                INSERT INTO jobs (id, tenant_id, run_id, plan_id, engagement_id, step_id, order_index, adapter, params)
                VALUES (:id,:t,:r,:p,:e,:sid,:ord,:ad,:pa)
            """), {
                "id": f"job_{uuid.uuid4().hex[:12]}", "t": e["tenant_id"], "r": rid, "p": p["id"], "e": e["id"],
                "sid": step.get("id"), "ord": idx, "ad": (step.get("tool_adapter") or step.get("id") or "echo"),
                "pa": json.dumps(step.get("params", {}))
            })
            insert_event(db, e["tenant_id"], rid, "job.queued", {"order": idx, "adapter": step.get("tool_adapter")})
        db.commit()
    except Exception:
        pass
    return {"id": rid, "engagement_id": e["id"], "plan_id": p["id"], "status": "running"}

@app.get("/v2/runs/{run_id}/events")
def events_stream(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(text("SELECT tenant_id FROM runs WHERE id=:id"), {"id": run_id}).mappings().first()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant(db, r["tenant_id"])

    async def gen():
        last_ts = None
        while True:
            await asyncio.sleep(0.6)
            with SessionLocal() as s:
                set_tenant(s, r["tenant_id"])
                if last_ts is None:
                    rows = s.execute(text("SELECT id,type,payload,created_at FROM run_events WHERE run_id=:rid ORDER BY created_at ASC LIMIT 50"),
                                     {"rid": run_id}).mappings().all()
                else:
                    rows = s.execute(text("SELECT id,type,payload,created_at FROM run_events WHERE run_id=:rid AND created_at > :ts ORDER BY created_at ASC LIMIT 50"),
                                     {"rid": run_id, "ts": last_ts}).mappings().all()
            for row in rows:
                last_ts = row["created_at"]
                yield {"event": row["type"], "id": row["id"], "data": json.dumps(row["payload"])}
            yield {"event":"keepalive", "data":"{}"}

    return EventSourceResponse(gen())

class ControlIn(BaseModel):
    action: str

@app.post("/v2/runs/{run_id}/control")
def run_control(run_id: str, body: ControlIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(text("SELECT tenant_id FROM runs WHERE id=:id"), {"id": run_id}).mappings().first()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant(db, r["tenant_id"])
    if body.action not in ("pause","resume","abort"):
        raise HTTPException(status_code=400, detail="invalid action")
    status_map = {"pause":"paused","resume":"running","abort":"aborted"}
    db.execute(text("UPDATE runs SET status=:s WHERE id=:r"), {"s": status_map[body.action], "r": run_id}); db.commit()
    insert_event(db, r["tenant_id"], run_id, f"run.{status_map[body.action]}", {"by":"user"})
    return {"ok": True, "status": status_map[body.action]}

class FindingIn(BaseModel):
    title: str
    severity: str
    description: str
    assets: Dict[str, Any] = Field(default_factory=dict)
    recommendation: Optional[str] = None
    tags: Dict[str, Any] = Field(default_factory=dict)

@app.post("/v2/runs/{run_id}/findings")
def findings_upsert(run_id: str, body: List[FindingIn], db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(text("SELECT tenant_id FROM runs WHERE id=:id"), {"id": run_id}).mappings().first()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant(db, r["tenant_id"])
    for f in body:
        db.execute(text("""
            INSERT INTO findings (id, tenant_id, run_id, title, severity, description, assets, recommendation, tags)
            VALUES (:id,:t,:r,:ti,:se,:de,:as,:re,:ta)
        """), {"id": f"vuln_{uuid.uuid4().hex[:10]}", "t": r["tenant_id"], "r": run_id,
               "ti": f.title, "se": f.severity, "de": f.description,
               "as": json.dumps(f.assets), "re": f.recommendation, "ta": json.dumps(f.tags)})
    db.commit()
    return {"ok": True}

@app.get("/v2/runs/{run_id}/findings")
def findings_list(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(text("SELECT tenant_id FROM runs WHERE id=:id"), {"id": run_id}).mappings().first()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant(db, r["tenant_id"])
    rows = db.execute(text("""
        SELECT id, title, severity, description, assets, recommendation, tags, created_at
        FROM findings WHERE run_id=:r ORDER BY created_at DESC
    """), {"r": run_id}).mappings().all()
    return {"findings": [dict(x) for x in rows]}

@app.post("/v2/runs/{run_id}/artifacts")
async def artifacts_upload(run_id: str, file: UploadFile = File(...), label: str = Form("evidence"), kind: str = Form("generic"),
                           db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(text("SELECT tenant_id FROM runs WHERE id=:id"), {"id": run_id}).mappings().first()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant(db, r["tenant_id"])

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{run_id}_{uuid.uuid4().hex[:8]}_{file.filename}"
    path = EVIDENCE_DIR / fname
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    db.execute(text("""
        INSERT INTO artifacts (id, tenant_id, run_id, kind, label, path)
        VALUES (:id,:t,:r,:k,:l,:p)
    """), {"id": f"art_{uuid.uuid4().hex[:10]}", "t": r["tenant_id"], "r": run_id, "k": kind, "l": label, "p": str(path)})
    db.commit()
    return {"ok": True, "path": str(path)}

@app.get("/v2/reports/run/{run_id}.json")
def report_json(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    r = db.execute(text("SELECT tenant_id, plan_id, engagement_id FROM runs WHERE id=:id"), {"id": run_id}).mappings().first()
    if not r: raise HTTPException(status_code=404, detail="run not found")
    set_tenant(db, r["tenant_id"])
    eng = db.execute(text("SELECT name, type, scope FROM engagements WHERE id=:id"), {"id": r["engagement_id"]}).mappings().first()
    plan = db.execute(text("SELECT data FROM plans WHERE id=:id"), {"id": r["plan_id"]}).mappings().first()
    findings = db.execute(text("SELECT id, title, severity, description, assets, recommendation, tags FROM findings WHERE run_id=:r"), {"r": run_id}).mappings().all()
    return {"run_id": run_id, "engagement": eng, "plan": plan["data"], "findings": [dict(x) for x in findings]}

@app.get("/v2/reports/run/{run_id}.md")
def report_md(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    data = report_json(run_id, db, principal)
    tpl = env.get_template("report_run.md.j2")
    return Response(content=tpl.render(**data), media_type="text/markdown")

@app.get("/v2/reports/run/{run_id}.html")
def report_html(run_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    data = report_json(run_id, db, principal)
    tpl = env.get_template("report_run.html.j2")
    return Response(content=tpl.render(**data), media_type="text/html")

class AgentTokenIn(BaseModel):
    tenant_id: str
    name: str
    expires_in_days: Optional[int] = 30

@app.post("/v2/agent_tokens")
def create_agent_token(body: AgentTokenIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant(db, body.tenant_id)
    raw = uuid.uuid4().hex + uuid.uuid4().hex
    aid = f"at_{uuid.uuid4().hex[:10]}"
    exp = "now() + interval '%s days'" % int(body.expires_in_days or 30)
    db.execute(text(f"""
        INSERT INTO agent_tokens (id, tenant_id, name, token_hash, expires_at, status, created_by)
        VALUES (:id, :t, :n, :h, {exp}, 'active', NULL)
    """), {"id": aid, "t": body.tenant_id, "n": body.name, "h": hashlib.sha256(raw.encode()).hexdigest()})
    db.commit()
    return {"id": aid, "token": raw}

def require_agent(db: Session, tenant_id: str, agent_id: str, agent_key: str):
    set_tenant(db, tenant_id)
    row = db.execute(text("SELECT id, agent_key_hash FROM agents WHERE id=:id"), {"id": agent_id}).mappings().first()
    if not row or row["agent_key_hash"] != hashlib.sha256(agent_key.encode()).hexdigest():
        raise HTTPException(status_code=401, detail="invalid agent credentials")

class AgentRegisterIn(BaseModel):
    enroll_token: str
    name: str
    kind: str = "cross_platform"

@app.post("/v2/agents/register")
def agent_register(body: AgentRegisterIn, x_tenant_id: str = Header(alias="X-Tenant-Id"), db: Session = Depends(get_db)):
    set_tenant(db, x_tenant_id)
    rows = db.execute(text("SELECT token_hash FROM agent_tokens WHERE tenant_id=:t AND status='active' ORDER BY created_at DESC"),
                      {"t": x_tenant_id}).mappings().all()
    th = hashlib.sha256(body.enroll_token.encode()).hexdigest()
    match = [r for r in rows if r["token_hash"] == th]
    if not match: raise HTTPException(status_code=401, detail="invalid enroll token")
    agent_id = f"agt_{uuid.uuid4().hex[:10]}"
    agent_key = uuid.uuid4().hex + uuid.uuid4().hex
    db.execute(text("INSERT INTO agents (id, tenant_id, name, kind, status, agent_key_hash) VALUES (:id,:t,:n,:k,'online',:h)"),
               {"id": agent_id, "t": x_tenant_id, "n": body.name, "k": body.kind, "h": hashlib.sha256(agent_key.encode()).hexdigest()})
    db.execute(text("UPDATE agent_tokens SET used_at=now() WHERE token_hash=:h"), {"h": th})
    db.commit()
    return {"agent_id": agent_id, "agent_key": agent_key}

@app.post("/v2/agents/heartbeat")
def agent_heartbeat(x_tenant_id: str = Header(alias="X-Tenant-Id"), x_agent_id: str = Header(alias="X-Agent-Id"), x_agent_key: str = Header(alias="X-Agent-Key"), db: Session = Depends(get_db)):
    require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    db.execute(text("UPDATE agents SET last_seen=now(), status='online' WHERE id=:id"), {"id": x_agent_id}); db.commit()
    return {"ok": True}

class LeaseIn(BaseModel):
    kinds: List[str] = Field(default_factory=lambda: ["cross_platform","kali_gateway"])

@app.post("/v2/agents/lease")
def agent_lease(body: LeaseIn, x_tenant_id: str = Header(alias="X-Tenant-Id"), x_agent_id: str = Header(alias="X-Agent-Id"), x_agent_key: str = Header(alias="X-Agent-Key"), db: Session = Depends(get_db)):
    require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    row = db.execute(text("""
        SELECT id, run_id, plan_id, engagement_id, adapter, params FROM jobs
        WHERE tenant_id = current_setting('app.current_tenant', true)
          AND status='queued'
        ORDER BY created_at ASC
        LIMIT 1
    """)).mappings().first()
    if not row: return Response(status_code=204)
    db.execute(text("UPDATE jobs SET status='leased', leased_by=:a, lease_expires_at=now() + interval '5 minutes' WHERE id=:id"),
               {"a": x_agent_id, "id": row["id"]}); db.commit()
    return {"id": row["id"], "adapter": row["adapter"], "params": row["params"]}

class JobEventIn(BaseModel):
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)

@app.post("/v2/jobs/{job_id}/events")
def job_events(job_id: str, body: JobEventIn, x_tenant_id: str = Header(alias="X-Tenant-Id"), x_agent_id: str = Header(alias="X-Agent-Id"), x_agent_key: str = Header(alias="X-Agent-Key"), db: Session = Depends(get_db)):
    require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    job = db.execute(text("SELECT id, run_id FROM jobs WHERE id=:id"), {"id": job_id}).mappings().first()
    if not job: raise HTTPException(status_code=404, detail="job not found")
    db.execute(text("INSERT INTO job_events (id, tenant_id, job_id, type, payload) VALUES (:id,:t,:j,:ty,:pl)"),
               {"id": f"je_{uuid.uuid4().hex[:10]}", "t": x_tenant_id, "j": job_id, "ty": body.type, "pl": json.dumps(body.payload)})
    insert_event(db, x_tenant_id, job["run_id"], f"job.{body.type.split('.')[-1]}", body.payload)
    return {"ok": True}

class JobCompleteIn(BaseModel):
    status: str
    result: Dict[str, Any] = Field(default_factory=dict)

@app.post("/v2/jobs/{job_id}/complete")
def job_complete(job_id: str, body: JobCompleteIn, x_tenant_id: str = Header(alias="X-Tenant-Id"), x_agent_id: str = Header(alias="X-Agent-Id"), x_agent_key: str = Header(alias="X-Agent-Key"), db: Session = Depends(get_db)):
    require_agent(db, x_tenant_id, x_agent_id, x_agent_key)
    job = db.execute(text("SELECT id, run_id FROM jobs WHERE id=:id"), {"id": job_id}).mappings().first()
    if not job: raise HTTPException(status_code=404, detail="job not found")
    db.execute(text("UPDATE jobs SET status=:s WHERE id=:id"), {"s": body.status, "id": job_id})
    insert_event(db, x_tenant_id, job["run_id"], f"job.{body.status}", body.result or {})
    row = db.execute(text("SELECT COUNT(*) FROM jobs WHERE run_id=:r AND status IN ('queued','leased','running')"), {"r": job["run_id"]}).scalar()
    if int(row or 0) == 0:
        db.execute(text("UPDATE runs SET status='completed' WHERE id=:r"), {"r": job["run_id"]})
        insert_event(db, x_tenant_id, job["run_id"], "run.completed", {"message": "All jobs finished"})
    db.commit()
    return {"ok": True}

@app.get("/v2/agents")
def agents_list(db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant(db, principal.tenant_id)
    rows = db.execute(text("""
        SELECT id, name, kind, status, last_seen
        FROM agents
        WHERE tenant_id = current_setting('app.current_tenant', true)
        ORDER BY last_seen DESC
        LIMIT 200
    """)).mappings().all()
    return {"agents": [dict(x) for x in rows]}

class AutoPlanIn(BaseModel):
    preferences: Dict[str, Any] = Field(default_factory=dict)
    risk_tier: str = "safe_active"

@app.post("/v2/engagements/{engagement_id}/plan/auto")
def plan_auto(engagement_id: str, body: AutoPlanIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    e = db.execute(text("SELECT id, tenant_id, type, scope FROM engagements WHERE id=:id"), {"id": engagement_id}).mappings().first()
    if not e: raise HTTPException(status_code=404, detail="engagement not found")
    set_tenant(db, e["tenant_id"])
    cat = load_catalog()
    ids = {i["id"] for i in cat["items"]}
    sel = []
    t = (e["type"] or "").lower()
    scope = e["scope"] or {}
    if t in ("network","external","internal"):
        if (scope.get("in_scope_cidrs")): sel += ["network_discovery_ping_sweep","network_nmap_tcp_top_1000"]
        if (scope.get("in_scope_domains")): sel += ["web_owasp_top10_core"]
    if t in ("web","webapp"): sel += ["web_owasp_top10_core"]
    if t in ("mobile","android","ios"): sel += ["mobile_static_analysis_apk"]
    packs = body.preferences.get("packs") or []
    try:
        pack_tests = []
        for pth in glob.glob(str(PACKS_DIR / "*.json")):
            with open(pth,"r") as f: pj = json.load(f)
            if pj.get("id") in packs: pack_tests += pj.get("tests",[])
        sel += pack_tests
    except Exception: pass
    sel = [s for s in dict.fromkeys(sel) if s in ids]
    return {"engagement_id": e["id"], "selected_tests": [{"id": s, "params": {}} for s in sel], "explanation": "Heuristic selection + packs", "policy_denies": []}

class FeedbackIn(BaseModel):
    engagement_id: Optional[str] = None
    plan_id: Optional[str] = None
    run_id: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

@app.post("/v2/brain/feedback")
def brain_feedback(body: FeedbackIn, db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant(db, principal.tenant_id)
    db.execute(text("""
        INSERT INTO brain_feedback (id, tenant_id, engagement_id, plan_id, run_id, rating, comment, created_by)
        VALUES (:id,:t,:e,:p,:r,:ra,:c,NULL)
    """), {"id": f"fb_{uuid.uuid4().hex[:10]}", "t": principal.tenant_id, "e": body.engagement_id, "p": body.plan_id, "r": body.run_id, "ra": body.rating, "c": body.comment})
    db.commit()
    return {"ok": True}

@app.get("/v2/brain/providers")
def brain_providers():
    return {"provider": "heuristic", "http_endpoint": False}

@app.get("/v2/runs/recent")
def runs_recent(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), principal: Principal = Depends(require_tenant)):
    set_tenant(db, principal.tenant_id)
    rows = db.execute(text("""
        SELECT r.id, r.engagement_id, r.plan_id, r.status,
               COALESCE(r.created_at, now()) AS created_at
        FROM runs r
        WHERE r.tenant_id = current_setting('app.current_tenant', true)
        ORDER BY created_at DESC
        LIMIT :lim
    """), {"lim": limit}).mappings().all()
    return {"runs": [dict(x) for x in rows]}
