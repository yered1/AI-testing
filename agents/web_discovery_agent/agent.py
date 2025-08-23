import os, time, json, uuid, requests, subprocess, shlex, tempfile, sys, pathlib

ORCH = os.environ.get("ORCH_URL","http://localhost:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"discover-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN", "")
ALLOW_ACTIVE = os.environ.get("ALLOW_ACTIVE_SCAN","0") in ("1","true","yes","on")

AGENT_ID = None
AGENT_KEY = None

def req_headers():
    return {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY, "Content-Type":"application/json"}

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN:
        print("[discovery] Missing AGENT_TOKEN", file=sys.stderr); sys.exit(2)
    r = requests.post(f"{ORCH}/v2/agents/register", json={
        "enroll_token": ENROLL_TOKEN,
        "name": AGENT_NAME,
        "kind": "web_discovery"
    }, headers={"X-Tenant-Id": TENANT}, timeout=20)
    r.raise_for_status()
    data = r.json(); print("[discovery] registered", data)
    global AGENT_ID, AGENT_KEY
    AGENT_ID = data["agent_id"]; AGENT_KEY = data["agent_key"]

def run_cmd(cmd: str, timeout=1800):
    print("[discovery] run:", cmd)
    try:
        cp = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)
        return {"rc": cp.returncode, "stdout": cp.stdout[-40000:], "stderr": cp.stderr[-40000:]}
    except Exception as e:
        return {"rc": -1, "error": str(e)}

def upload_artifact(job_id: str, path: str, label: str, kind: str="evidence"):
    files = {"file": (os.path.basename(path), open(path,"rb"))}
    data = {"label": label, "kind": kind}
    r = requests.post(f"{ORCH}/v2/jobs/{job_id}/artifacts", headers={"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY}, files=files, data=data, timeout=120)
    try:
        print("[discovery] uploaded", path, "->", r.status_code, r.text[:200])
    except Exception:
        pass

def adapter_dnsx_resolve(job_id: str, params: dict):
    domains = []
    if isinstance(params, dict):
        arr = params.get("domains") or params.get("targets") or []
        if isinstance(arr, list):
            domains = arr
    if not domains:
        return {"error":"no domains provided"}
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
        for d in domains: f.write(str(d).strip()+"\n")
        lst = f.name
    out = "dnsx.txt"
    cmd = f"dnsx -l {lst} -a -aaaa -cname -ns -mx -retry 2 -retries 2 -silent -r 1.1.1.1,8.8.8.8 -o {out}"
    res = run_cmd(cmd, timeout=900)
    if os.path.exists(out):
        upload_artifact(job_id, out, "dnsx_output", kind="text")
    return {"cmd": cmd, "exec": res}

def adapter_httpx_probe(job_id: str, params: dict):
    targets = []
    if isinstance(params, dict):
        targets = params.get("targets") or params.get("domains") or []
        if not isinstance(targets, list): targets = []
    if not targets: return {"error":"no targets provided"}
    # Normalize to URLs
    urls = [t if t.startswith("http") else f"https://{t}" for t in targets]
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
        for u in urls: f.write(u+"\n")
        lst = f.name
    out = "httpx.jsonl"
    cmd = f"httpx -l {lst} -follow-redirects -status-code -title -tech-detect -json -o {out}"
    res = run_cmd(cmd, timeout=1800)
    if os.path.exists(out):
        upload_artifact(job_id, out, "httpx_jsonl", kind="jsonl")
    return {"cmd": cmd, "exec": res, "sample": open(out,"r",errors="ignore").read().splitlines()[:5] if os.path.exists(out) else []}

ADAPTERS = {"dnsx_resolve": adapter_dnsx_resolve, "httpx_probe": adapter_httpx_probe}

def lease():
    # prefer lease2 to get richer context
    r = requests.post(f"{ORCH}/v2/agents/lease2", headers=req_headers(), json={"kinds":["web_discovery"]}, timeout=40)
    if r.status_code == 204:
        return None, None
    if r.status_code == 404 or r.status_code == 405:
        r = requests.post(f"{ORCH}/v2/agents/lease", headers=req_headers(), json={"kinds":["web_discovery"]}, timeout=40)
        if r.status_code == 204: return None, None
    r.raise_for_status()
    job = r.json()
    return job, job.get("run_id")

def main():
    register()
    while True:
        try:
            requests.post(f"{ORCH}/v2/agents/heartbeat", headers=req_headers(), timeout=10)
            job, run_id = lease()
            if not job:
                time.sleep(2); continue
            jid = job["id"]
            adapter = (job.get("adapter") or "").strip()
            params = job.get("params") or {}
            fn = ADAPTERS.get(adapter)
            if fn is None:
                result = {"adapter": adapter or "unknown", "note": "unsupported by discovery agent"}
            else:
                result = fn(jid, params)
            requests.post(f"{ORCH}/v2/jobs/{jid}/events", headers=req_headers(), json={"type":"job.started","payload":{"adapter":adapter}}, timeout=20)
            time.sleep(0.2)
            requests.post(f"{ORCH}/v2/jobs/{jid}/complete", headers=req_headers(), json={"status":"succeeded","result":result}, timeout=30)
        except Exception as e:
            print("[discovery] error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
