import os, time, json, requests, sys

API = os.environ.get("API", "http://localhost:8080").rstrip("/")
TENANT = os.environ.get("TENANT", "t_demo")
HDR = {
    "Content-Type": "application/json",
    "X-Dev-User": "ci",
    "X-Dev-Email": "ci@example.com",
    "X-Tenant-Id": TENANT,
}

def must(ok, msg):
    if not ok:
        print("ERROR:", msg)
        sys.exit(1)

def post(path, payload):
    r = requests.post(API + path, headers=HDR, json=payload, timeout=30)
    if r.status_code >= 400:
        print("POST", path, "->", r.status_code, r.text)
    r.raise_for_status()
    return r.json() if r.text else {}

def get(path):
    r = requests.get(API + path, headers=HDR, timeout=30)
    if r.status_code >= 400:
        print("GET", path, "->", r.status_code, r.text)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return r.text

def main():
    # health
    h = get("/health")
    print("health:", h)

    # create engagement
    eng = post("/v1/engagements", {"name":"ci","tenant_id":TENANT,"type":"web","scope":{"in_scope_domains":["example.com"]}})
    eid = eng.get("id")
    must(eid, "no engagement id")

    # autoplan
    ap = post(f"/v2/engagements/{eid}/plan/auto", {})
    selected = ap.get("selected_tests", [])
    must(isinstance(selected, list), "auto plan not a list")

    # validate
    sel = {"selected_tests": selected, "agents": {}, "risk_tier": "safe_active"}
    val = post(f"/v2/engagements/{eid}/plan/validate", sel)
    must("estimated_cost" in val, "no estimate in validate")

    # create plan
    plan = post(f"/v1/engagements/{eid}/plan", sel)
    pid = plan.get("id")
    must(pid, "no plan id")

    # start run
    run = post("/v1/tests", {"engagement_id": eid, "plan_id": pid})
    rid = run.get("id")
    must(rid, "no run id")

    # quotas
    qset = post("/v2/quotas", {"tenant_id": TENANT, "monthly_budget": 200, "per_plan_cap": 50})
    must(qset.get("ok"), "quota set failed")
    qget = get(f"/v2/quotas/{TENANT}")
    must(qget.get("tenant_id") == TENANT, "quota get mismatch")

    # approvals flow
    app = post("/v2/approvals", {"tenant_id": TENANT, "engagement_id": eid, "reason":"ci"})
    aid = app.get("id")
    must(aid, "no approval id")
    dec = post(f"/v2/approvals/{aid}/decide", {"tenant_id": TENANT, "decision":"approved"})
    must(dec.get("ok"), "approval decide failed")

    # findings and report
    fset = post(f"/v2/runs/{rid}/findings", [{"title":"CI Finding","severity":"low","description":"ok"}])
    must(fset.get("ok"), "findings upsert failed")
    rep = get(f"/v2/reports/run/{rid}.json")
    must(isinstance(rep, dict) and rep.get("run_id")==rid, "report json mismatch")

    # listings
    lst = get("/v2/runs/recent")
    must(isinstance(lst, dict) and "runs" in lst, "runs list failed")

    print("CI smoke OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
