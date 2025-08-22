import os, time, json, uuid, requests, hashlib, datetime

ORCH = os.environ.get("ORCH_URL", "http://localhost:8080")
TENANT = os.environ.get("TENANT_ID", "t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"devagent-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN", "")

AGENT_ID = None
AGENT_KEY = None

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN:
        raise SystemExit("AGENT_TOKEN is required")
    r = requests.post(f"{ORCH}/v2/agents/register", json={
        "enroll_token": ENROLL_TOKEN,
        "name": AGENT_NAME,
        "kind": "cross_platform"
    }, headers={"X-Tenant-Id": TENANT}, timeout=10)
    r.raise_for_status()
    data = r.json()
    AGENT_ID = data["agent_id"]
    AGENT_KEY = data["agent_key"]
    print(f"[agent] registered id={AGENT_ID}")

def hdr():
    return {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY, "Content-Type":"application/json"}

def lease_and_run():
    while True:
        try:
            # heartbeat
            requests.post(f"{ORCH}/v2/agents/heartbeat", headers=hdr(), timeout=10)
            # lease
            lr = requests.post(f"{ORCH}/v2/agents/lease", headers=hdr(), json={"kinds":["cross_platform"]}, timeout=20)
            if lr.status_code == 204:
                time.sleep(2); continue
            lr.raise_for_status()
            job = lr.json()
            job_id = job["id"]
            adapter = job["adapter"]
            params = job.get("params", {})
            requests.post(f"{ORCH}/v2/jobs/{job_id}/events", headers=hdr(), json={"type":"job.started","payload":{"adapter":adapter}}, timeout=10)

            # DEMO: adapters are simulated safely
            output = {"adapter": adapter, "echo": params, "ts": datetime.datetime.utcnow().isoformat()+"Z"}

            # report completion
            requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", headers=hdr(), json={"status":"succeeded","result":output}, timeout=10)
        except Exception as e:
            print("[agent] error:", e)
            time.sleep(2)

def main():
    register()
    lease_and_run()

if __name__ == "__main__":
    main()
