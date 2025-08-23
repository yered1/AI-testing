# File: AI-testing/agent/agent.py

- Size: 3855 bytes
- Kind: text
- SHA256: f420c11ce62a6b40710b5237fc99f0e12fa34304a75d44da1976fbbacfb9b179

## Python Imports

```
json, os, pathlib, requests, subprocess, sys, time, uuid
```

## Head (first 60 lines)

```
#!/usr/bin/env python3
import os, time, json, requests, subprocess, sys, pathlib, uuid

ORCH = os.environ.get("ORCH_URL","http://orchestrator:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
TOKEN = os.environ.get("AGENT_TOKEN","")
NAME = os.environ.get("AGENT_NAME", f"agent-{uuid.uuid4().hex[:6]}")
STATE_DIR = os.environ.get("STATE_DIR","/data")
STATE_FILE = os.path.join(STATE_DIR, "agent_state.json")
CAPS = os.environ.get("AGENT_CAPS","echo,http").split(",")

def headers():
    return {"X-Tenant-Id": TENANT, "X-Agent-Token": TOKEN, "X-Agent-Id": state().get("agent_id",""), "Content-Type":"application/json"}

def state():
    try:
        with open(STATE_FILE, "r") as f: return json.load(f)
    except Exception: return {}

def save_state(s):
    pathlib.Path(STATE_DIR).mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f: json.dump(s, f)

def register():
    print("[agent] registering...")
    r = requests.post(f"{ORCH}/v2/agents/register", json={"name": NAME, "capabilities": CAPS, "token": TOKEN}, headers={"X-Tenant-Id": TENANT}, timeout=10)
    r.raise_for_status()
    data = r.json()
    s = state(); s["agent_id"] = data["agent_id"]; save_state(s)
    print("[agent] registered as", data["agent_id"])

def heartbeat():
    aid = state().get("agent_id")
    if not aid: return
    try:
        requests.post(f"{ORCH}/v2/agents/heartbeat", json={"agent_id": aid, "capabilities": CAPS, "status":"idle"}, headers=headers(), timeout=10)
    except Exception as e:
        print("[agent] heartbeat error:", e)

def lease():
    aid = state().get("agent_id")
    if not aid: return None
    r = requests.post(f"{ORCH}/v2/agents/lease", json={"agent_id": aid, "capabilities": CAPS}, headers=headers(), timeout=20)
    if r.status_code == 204: return None
    r.raise_for_status(); return r.json()

def send_event(job_id, typ, payload):
    try:
        requests.post(f"{ORCH}/v2/jobs/{job_id}/events", json={"type": typ, "payload": payload}, headers=headers(), timeout=10)
    except Exception as e: print("[agent] event error:", e)

def complete(job_id, status, result):
    r = requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", json={"status": status, "result": result}, headers=headers(), timeout=30)
    r.raise_for_status()

def run_cmd(cmd, env=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, shell=True, env=env, timeout=300)
        return {"rc": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]}
    except Exception as e:
```

## Tail (last 60 lines)

```
    r = requests.post(f"{ORCH}/v2/agents/lease", json={"agent_id": aid, "capabilities": CAPS}, headers=headers(), timeout=20)
    if r.status_code == 204: return None
    r.raise_for_status(); return r.json()

def send_event(job_id, typ, payload):
    try:
        requests.post(f"{ORCH}/v2/jobs/{job_id}/events", json={"type": typ, "payload": payload}, headers=headers(), timeout=10)
    except Exception as e: print("[agent] event error:", e)

def complete(job_id, status, result):
    r = requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", json={"status": status, "result": result}, headers=headers(), timeout=30)
    r.raise_for_status()

def run_cmd(cmd, env=None):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, shell=True, env=env, timeout=300)
        return {"rc": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]}
    except Exception as e:
        return {"rc": 127, "stdout":"", "stderr": str(e)}

def execute(job):
    job_id = job["id"]
    payload = job["payload"]
    adapter = payload.get("tool_adapter") or "echo"
    params = payload.get("params", {})
    send_event(job_id, "job.started", {"adapter": adapter})

    if adapter == "echo":
        msg = json.dumps(params) if params else "hello"
        res = run_cmd(f"echo {msg}")
    elif adapter == "http_check":
        url = params.get("url","https://example.com")
        res = run_cmd(f"curl -sS -m 10 -i {url}")
    else:
        # unknown adapter => simulate
        res = {"rc":0, "stdout": f"Simulated adapter {adapter}", "stderr": ""}

    status = "succeeded" if res.get("rc",1) == 0 else "failed"
    send_event(job_id, "job.output", {"summary": res["stdout"][:200]})
    complete(job_id, status, res)

def main():
    if not TOKEN:
        print("[agent] AGENT_TOKEN is required"); sys.exit(2)
    if not state().get("agent_id"): register()
    next_hb = 0
    while True:
        now = time.time()
        if now >= next_hb:
            heartbeat(); next_hb = now + 10
        job = lease()
        if job:
            try:
                execute(job)
            except Exception as e:
                print("[agent] execute error:", e)
        time.sleep(2)

if __name__ == "__main__":
    main()
```

