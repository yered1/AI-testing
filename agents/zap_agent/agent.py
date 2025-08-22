import os, time, json, uuid, requests, tempfile, subprocess, shlex, sys

ORCH = os.environ.get("ORCH_URL","http://orchestrator:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"zap-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN", "")
ALLOW_ACTIVE = os.environ.get("ALLOW_ACTIVE_SCAN","0") in ("1","true","yes","on")

AGENT_ID = None
AGENT_KEY = None

def hdr():
    return {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY, "Content-Type":"application/json"}

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN:
        print("[zap-agent] Missing AGENT_TOKEN", file=sys.stderr); sys.exit(2)
    r = requests.post(f"{ORCH}/v2/agents/register", json={
        "enroll_token": ENROLL_TOKEN,
        "name": AGENT_NAME,
        "kind": "zap_web"
    }, headers={"X-Tenant-Id": TENANT}, timeout=20)
    r.raise_for_status()
    data = r.json()
    AGENT_ID = data["agent_id"]
    AGENT_KEY = data["agent_key"]
    print(f"[zap-agent] registered id={AGENT_ID}")

def run_cmd(cmd: str, timeout=7200):
    try:
        print("[zap-agent] running:", cmd)
        cp = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)
        return {"rc": cp.returncode, "stdout": cp.stdout[-20000:], "stderr": cp.stderr[-20000:]}
    except Exception as e:
        return {"rc": -1, "error": str(e)}

def adapter_zap_baseline(params):
    url = None
    if isinstance(params, dict):
        arr = params.get("domains") or params.get("targets") or []
        if isinstance(arr, list) and arr:
            u = arr[0]
            if not (u.startswith("http://") or u.startswith("https://")):
                u = "https://" + u
            url = u
    if not url:
        return {"error":"no target url"}
    # Baseline scan (non-intrusive). For intrusive, user must set ALLOW_ACTIVE_SCAN=1 and choose zap-full-scan.
    html = "zap_report.html"; json_out = "zap_report.json"
    if ALLOW_ACTIVE and params.get("mode") == "full":
        cmd = f"zap-full-scan.py -t {shlex.quote(url)} -r {html} -J {json_out} -m 10"
    else:
        cmd = f"zap-baseline.py -t {shlex.quote(url)} -I -m 10 -r {html} -J {json_out}"
    res = run_cmd(cmd, timeout=7200)
    # Read outputs if exist
    out = {"cmd": cmd, "exec": res}
    for fname in (html, json_out):
        try:
            if os.path.exists(fname):
                sz = os.path.getsize(fname)
                out.setdefault("artifacts", []).append({"name": fname, "size": sz})
                # We don't upload files here; orchestrator does not expose job->artifact upload yet.
                # Include a small tail of the JSON for visibility:
                if fname.endswith(".json") and sz < 2_000_000:
                    out["zap_json_tail"] = open(fname, "r", errors="ignore").read()[-5000:]
        except Exception:
            pass
    return out

ADAPTERS = {"zap_baseline": adapter_zap_baseline}

def run_job(job):
    job_id = job["id"]
    adapter = (job.get("adapter") or "").strip()
    params = job.get("params") or {}
    fn = ADAPTERS.get(adapter)
    if fn is None:
        result = {"adapter": adapter or "unknown", "params": params, "note": "adapter not supported by zap agent"}
    else:
        result = fn(params)
    requests.post(f"{ORCH}/v2/jobs/{job_id}/events", headers=hdr(), json={"type":"job.started","payload":{"adapter":adapter}}, timeout=20)
    time.sleep(0.2)
    requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", headers=hdr(), json={"status":"succeeded","result":result}, timeout=30)

def main():
    register()
    idle = 0
    while True:
        try:
            requests.post(f"{ORCH}/v2/agents/heartbeat", headers=hdr(), timeout=10)
            lr = requests.post(f"{ORCH}/v2/agents/lease", headers=hdr(), json={"kinds":["zap_web"]}, timeout=40)
            if lr.status_code == 204:
                idle += 1; time.sleep(2); continue
            idle = 0
            lr.raise_for_status()
            job = lr.json()
            run_job(job)
        except Exception as e:
            print("[zap-agent] error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
