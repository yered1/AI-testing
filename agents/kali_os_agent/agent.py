#!/usr/bin/env python3
# Kali OS Agent — polls orchestrator over HTTPS (v2 bus), runs allowlisted tools locally
import os, time, json, uuid, requests, subprocess, shlex, yaml, glob, pathlib, sys, platform

ORCH = os.environ.get("ORCH_URL","http://localhost:8080").rstrip("/")
TENANT = os.environ.get("TENANT_ID","t_demo")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN","")
AGENT_NAME = os.environ.get("AGENT_NAME", f"kali-os-{uuid.uuid4().hex[:6]}")
ALLOW_ACTIVE = os.environ.get("ALLOW_ACTIVE_SCAN","0").lower() in ("1","true","yes","on")
VERIFY_TLS = os.environ.get("CA_BUNDLE") or os.environ.get("REQUESTS_CA_BUNDLE") or True
WORKDIR = os.environ.get("AGENT_WORKDIR","/var/lib/kali-os-agent")
TOOLS_FILE = os.environ.get("TOOLS_FILE","/etc/kali-os-agent/tools.yaml")
KINDS = (os.environ.get("AGENT_KINDS") or "kali_os,kali_remote,cross_platform").split(",")

# agent credentials after register
AGENT_ID = None
AGENT_KEY = None

def mkdirs():
    for d in [WORKDIR, os.path.dirname(TOOLS_FILE)]:
        pathlib.Path(d).mkdir(parents=True, exist_ok=True)

def load_tools():
    try:
        with open(TOOLS_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

def hdr(base=None):
    h = {"X-Tenant-Id": TENANT, "Content-Type":"application/json"}
    if base: h.update(base)
    if AGENT_ID and AGENT_KEY:
        h["X-Agent-Id"] = AGENT_ID
        h["X-Agent-Key"] = AGENT_KEY
    return h

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN:
        print("[kali-os] Missing AGENT_TOKEN", file=sys.stderr); sys.exit(2)
    payload = {"enroll_token": ENROLL_TOKEN, "name": AGENT_NAME, "kind": "kali_os"}
    r = requests.post(f"{ORCH}/v2/agents/register", headers={"X-Tenant-Id": TENANT, "Content-Type":"application/json"}, json=payload, verify=VERIFY_TLS, timeout=20)
    r.raise_for_status()
    data = r.json()
    AGENT_ID = data.get("agent_id")
    AGENT_KEY = data.get("agent_key")
    print(f"[kali-os] registered id={AGENT_ID} name={AGENT_NAME} kinds={KINDS}")

def event(job_id, typ, payload):
    try:
        requests.post(f"{ORCH}/v2/jobs/{job_id}/events", headers=hdr(), json={"type":typ, "payload": payload}, verify=VERIFY_TLS, timeout=20)
    except Exception as e:
        print("[kali-os] event error:", e)

def complete(job_id, status, result):
    try:
        requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", headers=hdr(), json={"status":status, "result": result}, verify=VERIFY_TLS, timeout=60)
    except Exception as e:
        print("[kali-os] complete error:", e)

def upload_artifact(job_id, fpath):
    try:
        fname = os.path.basename(fpath)
        with open(fpath, "rb") as fp:
            files = {"file": (fname, fp)}
            # note: v2 artifacts endpoint may use form-data without content-type override
            h = {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY}
            r = requests.post(f"{ORCH}/v2/jobs/{job_id}/artifacts", headers=h, files=files, verify=VERIFY_TLS, timeout=120)
            if r.status_code >= 400:
                print("[kali-os] artifact upload failed", fpath, r.status_code, r.text[:200])
            else:
                print("[kali-os] artifact uploaded:", fname)
    except Exception as e:
        print("[kali-os] artifact upload error:", e)

def run_cmd(cmd, cwd, timeout=7200):
    try:
        print("[kali-os] running:", cmd)
        cp = subprocess.run(cmd if isinstance(cmd, list) else shlex.split(cmd), cwd=cwd, capture_output=True, text=True, timeout=timeout)
        out = {"rc": cp.returncode, "stdout": cp.stdout[-20000:], "stderr": cp.stderr[-20000:]}
        return out
    except subprocess.TimeoutExpired as e:
        return {"rc": -9, "error":"timeout", "stdout": e.stdout[-10000:] if e.stdout else "", "stderr": e.stderr[-10000:] if e.stderr else ""}
    except Exception as e:
        return {"rc": -1, "error": str(e)}

def render(template, params):
    # simple Python format with {key}
    try:
        return template.format(**(params or {}))
    except KeyError as e:
        missing = str(e).strip("'")
        raise RuntimeError(f"missing parameter: {missing}")

def select_tool(adapter, params, tools):
    # adapter may be 'nmap_tcp_top_1000' or 'run_tool' with params['tool']
    if adapter in tools.get("tools", {}):
        return adapter, tools["tools"][adapter]
    if adapter in ("run_tool","remote_tool","kali_run_tool"):
        toolname = (params or {}).get("tool")
        if toolname and toolname in tools.get("tools", {}):
            return toolname, tools["tools"][toolname]
    # common mapping
    if adapter == "nmap_tcp_top_1000" and "nmap_tcp_top_1000" in tools.get("tools", {}):
        return "nmap_tcp_top_1000", tools["tools"]["nmap_tcp_top_1000"]
    return None, None

def handle_job(job, tools):
    job_id = job["id"]
    adapter = (job.get("adapter") or "").strip()
    params = job.get("params") or {}
    work = os.path.join(WORKDIR, "jobs", job_id)
    pathlib.Path(work).mkdir(parents=True, exist_ok=True)

    # pick tool & template
    tname, tdef = select_tool(adapter, params, tools)
    if not tdef:
        event(job_id, "agent.error", {"msg":"no tool mapping for adapter", "adapter":adapter, "params":params})
        complete(job_id, "failed", {"error":"no tool mapping", "adapter":adapter})
        return

    # active check
    active = bool(tdef.get("active", False))
    if active and not ALLOW_ACTIVE:
        complete(job_id, "skipped", {"note":"dry-run (ALLOW_ACTIVE_SCAN=0)", "adapter":adapter, "tool":tname})
        return

    # build command
    try:
        cmd = render(tdef.get("cmd","").strip(), params)
    except Exception as e:
        complete(job_id, "failed", {"error": f"render error: {e}", "adapter":adapter, "tool":tname})
        return

    timeout = int(tdef.get("timeout", 7200))
    event(job_id, "job.started", {"adapter":adapter, "tool":tname, "cmd":cmd})
    res = run_cmd(cmd, cwd=work, timeout=timeout)

    # collect artifacts
    art_globs = tdef.get("artifacts", [])
    uploaded = []
    for g in art_globs:
        for fp in glob.glob(os.path.join(work, g)):
            upload_artifact(job_id, fp)
            uploaded.append(os.path.basename(fp))

    # result payload
    result = {"adapter":adapter, "tool":tname, "cmd":cmd, "exec":res, "artifacts":uploaded, "workdir":work}
    status = "succeeded" if res.get("rc",1) == 0 else "failed"
    complete(job_id, status, result)

def loop():
    tools = load_tools()
    idle = 0
    while True:
        try:
            # heartbeat
            try:
                requests.post(f"{ORCH}/v2/agents/heartbeat", headers=hdr(), json={}, verify=VERIFY_TLS, timeout=10)
            except Exception as e:
                # just log
                print("[kali-os] heartbeat error:", e)

            # lease job (prefer lease2)
            try:
                lr = requests.post(f"{ORCH}/v2/agents/lease", headers=hdr(), json={"kinds": KINDS}, verify=VERIFY_TLS, timeout=40)
                if lr.status_code == 204:
                    idle += 1; time.sleep(2); continue
                lr.raise_for_status()
                job = lr.json()
            except Exception as e:
                print("[kali-os] lease error:", e)
                time.sleep(3); continue

            idle = 0
            handle_job(job, tools)
        except KeyboardInterrupt:
            print("[kali-os] exiting"); return
        except Exception as e:
            print("[kali-os] loop error:", e)
            time.sleep(2)

def main():
    print(f"[kali-os] starting on {platform.platform()} py{sys.version.split()[0]}")
    mkdirs()
    if not os.path.exists(TOOLS_FILE):
        # seed with defaults
        default = {
            "tools": {
                "nmap_tcp_top_1000": {
                    "cmd": "nmap -Pn --top-ports 1000 -T3 {target} -oN nmap_top1000.txt",
                    "active": True,
                    "timeout": 7200,
                    "artifacts": ["nmap_top1000.txt"]
                },
                "ffuf_dirb": {
                    "cmd": "ffuf -u {url}/FUZZ -w {wordlist} -mc 200,204,301,302,307,401,403 -o ffuf.json -of json",
                    "active": True,
                    "timeout": 3600,
                    "artifacts": ["ffuf.json"]
                },
                "gobuster_dir": {
                    "cmd": "gobuster dir -u {url} -w {wordlist} -t 50 -o gobuster.txt",
                    "active": True,
                    "timeout": 3600,
                    "artifacts": ["gobuster.txt"]
                },
                "sqlmap_basic": {
                    "cmd": "sqlmap -u {url} --batch --risk=1 --level=1 --output-dir=.",
                    "active": True,
                    "timeout": 14400,
                    "artifacts": ["output/*"]
                }
            }
        }
        pathlib.Path(TOOLS_FILE).write_text(yaml.safe_dump(default), encoding="utf-8")
        print("[kali-os] seeded tools.yaml at", TOOLS_FILE)
    register()
    loop()

if __name__ == "__main__":
    main()
