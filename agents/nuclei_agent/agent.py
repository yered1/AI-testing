import os, time, json, uuid, requests, tempfile, subprocess, shlex, sys, pathlib

ORCH = os.environ.get("ORCH_URL","http://orchestrator:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"nuclei-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN", "")

AGENT_ID = None
AGENT_KEY = None

def hdr():
    return {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY, "Content-Type":"application/json"}

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN:
        print("[nuclei-agent] Missing AGENT_TOKEN", file=sys.stderr); sys.exit(2)
    r = requests.post(f"{ORCH}/v2/agents/register", json={
        "enroll_token": ENROLL_TOKEN,
        "name": AGENT_NAME,
        "kind": "nuclei"
    }, headers={"X-Tenant-Id": TENANT}, timeout=20)
    r.raise_for_status()
    data = r.json()
    AGENT_ID = data["agent_id"]
    AGENT_KEY = data["agent_key"]
    print(f"[nuclei-agent] registered id={AGENT_ID}")

def run_cmd(cmd: str, timeout=7200):
    try:
        print("[nuclei-agent] running:", cmd)
        cp = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)
        return {"rc": cp.returncode, "stdout": cp.stdout[-20000:], "stderr": cp.stderr[-20000:]}
    except Exception as e:
        return {"rc": -1, "error": str(e)}

def adapter_nuclei_default(params):
    targets = []
    if isinstance(params, dict):
        targets = params.get("targets") or params.get("domains") or []
        if not isinstance(targets, list): targets = []
    if not targets:
        return {"error":"no targets provided"}
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
        for t in targets:
            if t:
                f.write((t if t.startswith("http") else f"https://{t}") + "\\n")
        lst = f.name
    out = "nuclei.jsonl"
    cmd = f"nuclei -l {lst} -headless -jsonl -o {out} -severity medium,high,critical -rl 50 -c 50"
    res = run_cmd(cmd, timeout=7200)
    findings = []
    try:
        if os.path.exists(out):
            for line in open(out, "r", errors="ignore"):
                try:
                    findings.append(json.loads(line.strip()))
                except Exception:
                    pass
    except Exception:
        pass
    sample = findings[:20]
    return {"cmd": cmd, "exec": res, "count": len(findings), "sample": sample}

ADAPTERS = {"nuclei_default": adapter_nuclei_default}

def run_job(job):
    job_id = job["id"]
    adapter = (job.get("adapter") or "").strip()
    params = job.get("params") or {}
    fn = ADAPTERS.get(adapter)
    if fn is None:
        result = {"adapter": adapter or "unknown", "params": params, "note": "adapter not supported by nuclei agent"}
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
            lr = requests.post(f"{ORCH}/v2/agents/lease", headers=hdr(), json={"kinds":["nuclei"]}, timeout=40)
            if lr.status_code == 204:
                idle += 1; time.sleep(2); continue
            idle = 0
            lr.raise_for_status()
            job = lr.json()
            run_job(job)
        except Exception as e:
            print("[nuclei-agent] error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
