import os, time, json, uuid, requests, subprocess, shlex, sys

ORCH = os.environ.get("ORCH_URL","http://localhost:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"zapv2-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN", "")
ALLOW_ACTIVE = os.environ.get("ALLOW_ACTIVE_SCAN","0") in ("1","true","yes","on")

AGENT_ID = None
AGENT_KEY = None

def hdr():
    return {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY}

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN:
        print("[zapv2] Missing AGENT_TOKEN", file=sys.stderr); sys.exit(2)
    r = requests.post(f"{ORCH}/v2/agents/register", json={
        "enroll_token": ENROLL_TOKEN,
        "name": AGENT_NAME,
        "kind": "zap_web"
    }, headers={"X-Tenant-Id": TENANT}, timeout=30)
    r.raise_for_status()
    data = r.json()
    AGENT_ID = data["agent_id"]
    AGENT_KEY = data["agent_key"]
    print(f"[zapv2] registered id={AGENT_ID}")

def run_cmd(cmd: str, timeout=7200):
    try:
        print("[zapv2] run:", cmd)
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
        return {"error": "no target url"}
    html = "zap_report.html"; json_out = "zap_report.json"
    if ALLOW_ACTIVE and params.get("mode") == "full":
        cmd = f"zap-full-scan.py -t {shlex.quote(url)} -r {html} -J {json_out} -m 10"
    else:
        cmd = f"zap-baseline.py -t {shlex.quote(url)} -I -m 10 -r {html} -J {json_out}"
    res = run_cmd(cmd, timeout=7200)
    arts = []
    for fname, kind in [(html,"html"), (json_out,"json")]:
        if os.path.exists(fname):
            arts.append((fname, kind))
    return {"cmd": cmd, "exec": res, "artifacts": arts}

ADAPTERS = {"zap_baseline": adapter_zap_baseline}

def lease():
    # try lease2 first
    try:
        r = requests.post(f"{ORCH}/v2/agents/lease2", headers={**hdr(), "Content-Type":"application/json"}, json={"kinds":["zap"]}, timeout=40)
        if r.status_code == 204: return None
        if r.status_code == 404: raise Exception("lease2 not found")
        r.raise_for_status()
        j = r.json()
        j["_lease2"] = True
        return j
    except Exception as e:
        # fallback to lease
        r = requests.post(f"{ORCH}/v2/agents/lease", headers={**hdr(), "Content-Type":"application/json"}, json={"kinds":["zap_web"]}, timeout=40)
        if r.status_code == 204: return None
        r.raise_for_status()
        j = r.json()
        j["_lease2"] = False
        return j

def upload_artifacts(job_id, artifacts):
    for (path, kind) in artifacts or []:
        try:
            with open(path, "rb") as f:
                files = {"file": (os.path.basename(path), f, "application/octet-stream")}
                data = {"label": f"zap_{kind}", "kind": kind}
                r = requests.post(f"{ORCH}/v2/jobs/{job_id}/artifacts", headers=hdr(), files=files, data=data, timeout=120)
                print("[zapv2] upload", path, "->", r.status_code)
        except Exception as e:
            print("[zapv2] upload error", path, e)

def run_job(job):
    job_id = job["id"]
    adapter = (job.get("adapter") or "").strip()
    params = job.get("params") or {}
    fn = ADAPTERS.get(adapter)
    if fn is None:
        result = {"adapter": adapter or "unknown", "params": params, "note": "adapter not supported by zapv2"}
    else:
        result = fn(params)
    # events + upload artifacts (if any)
    requests.post(f"{ORCH}/v2/jobs/{job_id}/events", headers={**hdr(), "Content-Type":"application/json"}, json={"type":"job.started","payload":{"adapter":adapter}}, timeout=20)
    if isinstance(result, dict) and result.get("artifacts"):
        upload_artifacts(job_id, result["artifacts"])
    requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", headers={**hdr(), "Content-Type":"application/json"}, json={"status":"succeeded","result":{k:v for k,v in result.items() if k!='artifacts'}}, timeout=60)

def main():
    register()
    while True:
        try:
            requests.post(f"{ORCH}/v2/agents/heartbeat", headers=hdr(), timeout=10)
            job = lease()
            if not job:
                time.sleep(2); continue
            run_job(job)
        except Exception as e:
            print("[zapv2] error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
