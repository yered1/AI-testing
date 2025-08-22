import os, time, json, uuid, requests, datetime, sys, subprocess, shlex

ORCH = os.environ.get("ORCH_URL","http://localhost:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"devext-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN", "")
ALLOW_ACTIVE = os.environ.get("ALLOW_ACTIVE_SCAN","0") in ("1","true","yes","on")

AGENT_ID = None
AGENT_KEY = None

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN:
        print("[agent-ext] Missing AGENT_TOKEN", file=sys.stderr); sys.exit(2)
    r = requests.post(f"{ORCH}/v2/agents/register", json={
        "enroll_token": ENROLL_TOKEN,
        "name": AGENT_NAME,
        "kind": "cross_platform"
    }, headers={"X-Tenant-Id": TENANT}, timeout=10)
    r.raise_for_status()
    data = r.json()
    AGENT_ID = data["agent_id"]
    AGENT_KEY = data["agent_key"]
    print(f"[agent-ext] registered id={AGENT_ID}")

def hdr():
    return {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY, "Content-Type":"application/json"}

def run_cmd(cmd: str, timeout: int = 900):
    try:
        cp = subprocess.run(shlex.split(cmd), capture_output=True, timeout=timeout, text=True)
        return {"rc": cp.returncode, "stdout": cp.stdout[-20000:], "stderr": cp.stderr[-20000:]}
    except Exception as e:
        return {"rc": -1, "error": str(e)}

def adapter_echo(params):
    return {"echo": params, "ts": datetime.datetime.utcnow().isoformat()+"Z"}

def adapter_nmap_tcp_top_1000(params):
    targets = []
    if isinstance(params, dict):
        arr = params.get("targets") or []
        if isinstance(arr, list): targets = arr
    target = targets[0] if targets else None
    cmd = ["nmap","-Pn","--top-ports","1000","-T3"]
    if target: cmd += [target]
    cmd_str = " ".join(cmd)
    if ALLOW_ACTIVE:
        res = run_cmd(cmd_str, timeout=3600)
        return {"adapter":"nmap_tcp_top_1000","command":cmd_str, "result":res}
    return {"adapter":"nmap_tcp_top_1000","command":cmd_str,"note":"dry-run (ALLOW_ACTIVE_SCAN=0)"}

ADAPTERS = {
    "echo": adapter_echo,
    "nmap_tcp_top_1000": adapter_nmap_tcp_top_1000,
}

def run_job(job):
    job_id = job["id"]
    adapter = (job.get("adapter") or "").strip()
    params = job.get("params") or {}
    fn = ADAPTERS.get(adapter)
    if fn is None:
        result = {"adapter": adapter or "unknown","params": params, "note": "no adapter implemented"}
    else:
        result = fn(params)
    requests.post(f"{ORCH}/v2/jobs/{job_id}/events", headers=hdr(), json={"type":"job.started","payload":{"adapter":adapter}}, timeout=10)
    time.sleep(0.2)
    requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", headers=hdr(), json={"status":"succeeded","result":result}, timeout=30)

def main():
    register()
    idle = 0
    while True:
        try:
            requests.post(f"{ORCH}/v2/agents/heartbeat", headers=hdr(), timeout=10)
            lr = requests.post(f"{ORCH}/v2/agents/lease", headers=hdr(), json={"kinds":["cross_platform","kali_gateway"]}, timeout=30)
            if lr.status_code == 204:
                idle += 1; time.sleep(2); continue
            idle = 0
            lr.raise_for_status()
            job = lr.json()
            run_job(job)
        except Exception as e:
            print("[agent-ext] error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
