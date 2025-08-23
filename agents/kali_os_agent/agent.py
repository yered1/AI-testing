#!/usr/bin/env python3
import os, time, json, uuid, requests, subprocess, shlex, glob, sys, yaml

ORCH = os.environ.get("ORCH_URL","http://orchestrator:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
NAME = os.environ.get("AGENT_NAME", f"kali-os-{uuid.uuid4().hex[:6]}")
TOKEN = os.environ.get("AGENT_TOKEN","")
ALLOW_ACTIVE = os.environ.get("ALLOW_ACTIVE_SCAN","0") in ("1","true","yes","on")

AGENT_ID = None
AGENT_KEY = None

TOOLS_FILE = os.environ.get("TOOLS_FILE", "/etc/kali-os-agent/tools.yaml")

def hdr():
    return {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID or "", "X-Agent-Key": AGENT_KEY or "", "Content-Type":"application/json"}

def register():
    global AGENT_ID, AGENT_KEY
    if not TOKEN:
        print("[kali-os] Missing AGENT_TOKEN", file=sys.stderr); sys.exit(2)
    r = requests.post(f"{ORCH}/v2/agents/register", json={
        "enroll_token": TOKEN,
        "name": NAME,
        "kind": "kali_os"
    }, headers={"X-Tenant-Id": TENANT}, timeout=30)
    r.raise_for_status()
    data = r.json()
    AGENT_ID = data["agent_id"]; AGENT_KEY = data["agent_key"]
    print(f"[kali-os] registered id={AGENT_ID}")

def job_event(job_id, etype, payload):
    try:
        requests.post(f"{ORCH}/v2/jobs/{job_id}/events", headers=hdr(), json={"type": etype, "payload": payload}, timeout=20)
    except Exception as e:
        print("[kali-os] job_event error:", e)

def job_complete(job_id, status, result):
    try:
        requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", headers=hdr(), json={"status": status, "result": result}, timeout=40)
    except Exception as e:
        print("[kali-os] job_complete error:", e)

def upload_artifact(job_id, path):
    try:
        with open(path, "rb") as f:
            files = {"file": (os.path.basename(path), f)}
            # agent-authenticated artifact upload (your API expects JSON; if multipart is required, adjust accordingly)
            requests.post(f"{ORCH}/v2/jobs/{job_id}/artifacts", headers={"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY}, files=files, timeout=120)
            print(f"[kali-os] uploaded artifact {path}")
    except Exception as e:
        print("[kali-os] upload artifact error:", e)

def load_tools():
    if not os.path.exists(TOOLS_FILE):
        return {}
    with open(TOOLS_FILE, "r") as f:
        return yaml.safe_load(f) or {}

def render_cmd(template, params):
    # very basic safe param interpolation
    def repl(m):
        key = m.group(1)
        val = params.get(key, "")
        if isinstance(val, list):
            return " ".join(shlex.quote(str(x)) for x in val)
        return shlex.quote(str(val))
    import re
    return re.sub(r"\{\{(\w+)\}\}", repl, template)

def run_cmd(cmd, timeout=7200):
    print("[kali-os] run:", cmd)
    try:
        cp = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"rc": cp.returncode, "stdout": cp.stdout[-20000:], "stderr": cp.stderr[-20000:]}
    except subprocess.TimeoutExpired as e:
        return {"rc": -2, "timeout": True, "msg": str(e)}
    except Exception as e:
        return {"rc": -1, "error": str(e)}

def adapter_nmap_tcp_top_1000(job_id, params):
    target = params.get("target") or params.get("host") or params.get("domain")
    if not target:
        return {"error":"missing target"}    
    if not ALLOW_ACTIVE:
        return {"note":"active scan blocked (ALLOW_ACTIVE_SCAN=0)","would_run": f"nmap -Pn --top-ports 1000 -T3 {shlex.quote(target)} -oN nmap_top1000.txt -oX nmap_top1000.xml"}
    cmd = f"nmap -Pn --top-ports 1000 -T3 {shlex.quote(target)} -oN nmap_top1000.txt -oX nmap_top1000.xml"
    res = run_cmd(cmd, timeout=10800)
    for art in ["nmap_top1000.txt","nmap_top1000.xml"]:
        if os.path.exists(art): upload_artifact(job_id, art)
    return {"cmd": cmd, "exec": res}

def adapter_run_tool(job_id, params):
    tool = params.get("tool")
    tools = load_tools()
    spec = tools.get(tool or "")
    if not spec:
        return {"error": f"tool '{tool}' not in allowlist"}
    if spec.get("active") and not ALLOW_ACTIVE:
        return {"note": f"active tool '{tool}' blocked (ALLOW_ACTIVE_SCAN=0)"}
    tmpl = spec.get("cmd","")
    cmd = render_cmd(tmpl, params)
    res = run_cmd(cmd, timeout=int(spec.get("timeout", 7200)))
    for pat in spec.get("artifacts", []):
        for path in glob.glob(pat):
            upload_artifact(job_id, path)
    return {"tool": tool, "cmd": cmd, "exec": res}

def run_job(job):
    job_id = job.get("id")
    adapter = (job.get("adapter") or "").strip()
    params = job.get("params") or {}
    job_event(job_id, "job.started", {"adapter": adapter})
    try:
        if adapter == "nmap_tcp_top_1000":
            result = adapter_nmap_tcp_top_1000(job_id, params)
        elif adapter == "run_tool":
            result = adapter_run_tool(job_id, params)
        else:
            result = {"error": f"adapter '{adapter}' not supported by kali_os agent"}
        job_complete(job_id, "succeeded", result)
    except Exception as e:
        job_complete(job_id, "failed", {"error": str(e)})

def main():
    register()
    idle = 0
    while True:
        try:
            requests.post(f"{ORCH}/v2/agents/heartbeat", headers=hdr(), timeout=10)
            # prefer lease2
            lr = requests.post(f"{ORCH}/v2/agents/lease2", headers=hdr(), json={"kinds":["kali_os"]}, timeout=40)
            if lr.status_code == 404:
                lr = requests.post(f"{ORCH}/v2/agents/lease", headers=hdr(), json={"kinds":["kali_os"]}, timeout=40)
            if lr.status_code == 204:
                idle += 1; time.sleep(min(10, 1+idle)); continue
            idle = 0
            lr.raise_for_status()
            job = lr.json()
            run_job(job)
        except Exception as e:
            print("[kali-os] loop error:", e)
            time.sleep(3)

if __name__ == "__main__":
    main()
