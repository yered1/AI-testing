import os, time, json, uuid, requests, datetime, sys

ORCH = os.environ.get("ORCH_URL","http://localhost:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"devagent-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN", "")

AGENT_ID = None
AGENT_KEY = None

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN:
        print("[agent] Missing AGENT_TOKEN", file=sys.stderr); sys.exit(2)
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

def run_job(job):
    job_id = job["id"]
    adapter = job.get("adapter")
    params = job.get("params") or {}
    if adapter == "echo":
        result = {"echo": params, "ts": datetime.datetime.utcnow().isoformat()+"Z"}
    elif adapter == "nmap_tcp_top_1000":
        target = None
        if isinstance(params, dict):
            arr = params.get("targets") or []
            if isinstance(arr, list) and arr:
                target = arr[0]
        cmd = ["nmap","-Pn","--top-ports","1000","-T3"]
        if target: cmd += [target]
        result = {"adapter":"nmap_tcp_top_1000","command":" ".join(cmd),"note":"dev agent demo; ensure authorization before scanning."}
    else:
        result = {"adapter": adapter or "unknown", "params": params, "note": "No-op demo"}
    requests.post(f"{ORCH}/v2/jobs/{job_id}/events", headers=hdr(), json={"type":"job.started","payload":{"adapter":adapter}}, timeout=10)
    time.sleep(0.5)
    requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", headers=hdr(), json={"status":"succeeded","result":result}, timeout=10)

def main():
    register()
    while True:
        try:
            requests.post(f"{ORCH}/v2/agents/heartbeat", headers=hdr(), timeout=10)
            lr = requests.post(f"{ORCH}/v2/agents/lease", headers=hdr(), json={"kinds":["cross_platform","kali_gateway"]}, timeout=20)
            if lr.status_code == 204:
                time.sleep(2); continue
            lr.raise_for_status()
            job = lr.json()
            run_job(job)
        except Exception as e:
            print("[agent] error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
