import os, time, json, uuid, requests, base64, tempfile, subprocess, shlex, sys, pathlib, re
from typing import Dict, Any, List

ORCH = os.environ.get("ORCH_URL","http://orchestrator:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"kali-remote-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN","")
ALLOW_ACTIVE = os.environ.get("ALLOW_ACTIVE_SCAN","0") in ("1","true","yes","on")
SSH_HOST = os.environ.get("SSH_HOST")
SSH_USER = os.environ.get("SSH_USER","kali")
SSH_PORT = int(os.environ.get("SSH_PORT","22"))
SSH_KEY_B64 = os.environ.get("SSH_KEY_BASE64","")
SSH_PASSWORD = os.environ.get("SSH_PASSWORD","")

AGENT_ID=None; AGENT_KEY=None

TOOLS_PATH=pathlib.Path("/app/agent/tools.yaml")

def hdr():
    return {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY, "Content-Type":"application/json"}

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN:
        print("[kali-remote] Missing AGENT_TOKEN", file=sys.stderr); sys.exit(2)
    r = requests.post(f"{ORCH}/v2/agents/register", json={
        "enroll_token": ENROLL_TOKEN, "name": AGENT_NAME, "kind":"kali_remote"
    }, headers={"X-Tenant-Id": TENANT}, timeout=20)
    r.raise_for_status()
    data = r.json()
    AGENT_ID=data["agent_id"]; AGENT_KEY=data["agent_key"]
    print(f"[kali-remote] registered id={AGENT_ID}")

def ssh_base():
    if not SSH_HOST:
        raise RuntimeError("SSH_HOST not set")
    base = f"ssh -p {SSH_PORT} -o StrictHostKeyChecking=no "
    if SSH_KEY_B64:
        key_path="/tmp/sshkey"
        open(key_path,"wb").write(base64.b64decode(SSH_KEY_B64))
        os.chmod(key_path,0o600)
        base += f"-i {key_path} "
    return base + f"{SSH_USER}@{SSH_HOST} "

def run_remote(cmd, timeout=7200):
    full = ssh_base() + shlex.quote(cmd)
    print("[kali-remote] SSH:", full)
    cp = subprocess.run(full, shell=True, capture_output=True, text=True, timeout=timeout)
    return {"rc": cp.returncode, "stdout": cp.stdout[-20000:], "stderr": cp.stderr[-20000:]}

def sftp_get(remote_path, local_path):
    base = f"scp -P {SSH_PORT} -o StrictHostKeyChecking=no "
    if SSH_KEY_B64:
        key_path="/tmp/sshkey"
        base += f"-i {key_path} "
    full = f"{base}{SSH_USER}@{SSH_HOST}:{shlex.quote(remote_path)} {shlex.quote(local_path)}"
    cp = subprocess.run(full, shell=True, capture_output=True, text=True, timeout=600)
    return cp.returncode==0, cp.stdout, cp.stderr

def load_tools():
    import yaml
    try:
        data = yaml.safe_load(open(TOOLS_PATH,"r"))
        return data or {}
    except Exception as e:
        print("[kali-remote] tools.yaml load failed:", e); return {}

def adapter_nmap_top_1000(params:Dict[str,Any]):
    targets = params.get("targets") or params.get("domains") or []
    if not isinstance(targets, list) or not targets:
        return {"error":"no targets provided"}
    if not ALLOW_ACTIVE:
        return {"note":"dry-run","cmd":"nmap -Pn --top-ports 1000 -T3 ... (blocked unless ALLOW_ACTIVE_SCAN=1)"}
    cmd = "nmap -Pn --top-ports 1000 -T3 -oN /tmp/nmap_top1000.txt " + " ".join(shlex.quote(t) for t in targets)
    res = run_remote(cmd)
    # fetch artifact
    ok, out, err = sftp_get("/tmp/nmap_top1000.txt","nmap_top1000.txt")
    art = []
    if ok: art.append({"name":"nmap_top1000.txt","size": os.path.getsize("nmap_top1000.txt")})
    return {"cmd": cmd, "exec": res, "artifacts": art}

def adapter_run_tool(params:Dict[str,Any]):
    tools=load_tools()
    name = params.get("tool")
    spec = tools.get(name or "",{})
    if not spec:
        return {"error": f"tool '{name}' not in allowlist"}
    # active guard
    if spec.get("active", False) and not ALLOW_ACTIVE:
        return {"note":"dry-run", "cmd": spec.get("cmd")}
    # substitute params
    cmd_tmpl = spec.get("cmd")
    # naive substitution
    for k,v in (params.get("args") or {}).items():
        cmd_tmpl = cmd_tmpl.replace("{{"+k+"}}", str(v))
    res = run_remote(cmd_tmpl)
    art = []
    for path in spec.get("artifacts", []):
        lp = os.path.basename(path)
        ok, out, err = sftp_get(path, lp)
        if ok:
            art.append({"name": lp, "size": os.path.getsize(lp)})
    return {"cmd": cmd_tmpl, "exec": res, "artifacts": art}

ADAPTERS = {
    "nmap_tcp_top_1000": adapter_nmap_top_1000,
    "run_tool": adapter_run_tool,
}

def upload_artifacts(job_id, artifacts):
    for a in artifacts or []:
        path = a.get("name")
        if not path or not os.path.exists(path):
            continue
        files={"file": open(path,"rb")}
        r = requests.post(f"{ORCH}/v2/jobs/{job_id}/artifacts", headers=hdr(), files=files, timeout=60)
        try: r.raise_for_status()
        except Exception as e: print("[kali-remote] artifact upload failed:", e, path)

def run_job(job):
    job_id = job["id"]
    adapter = (job.get("adapter") or "").strip()
    params = job.get("params") or {}
    fn = ADAPTERS.get(adapter)
    if fn is None:
        result = {"adapter": adapter or "unknown", "params": params, "note": "adapter not supported by kali_remote"}
    else:
        result = fn(params)
    requests.post(f"{ORCH}/v2/jobs/{job_id}/events", headers=hdr(), json={"type":"job.started","payload":{"adapter":adapter}}, timeout=20)
    time.sleep(0.2)
    upload_artifacts(job_id, result.get("artifacts"))
    requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", headers=hdr(), json={"status":"succeeded","result":result}, timeout=30)

def main():
    register()
    while True:
        try:
            # lease2 preferred
            lr = requests.post(f"{ORCH}/v2/agents/lease2", headers=hdr(), json={"kinds":["kali_remote"]}, timeout=40)
            if lr.status_code == 204:
                time.sleep(2); continue
            if lr.status_code >= 400:
                # fallback
                lr = requests.post(f"{ORCH}/v2/agents/lease", headers=hdr(), json={"kinds":["kali_remote"]}, timeout=40)
            if lr.status_code == 204:
                time.sleep(2); continue
            lr.raise_for_status()
            job = lr.json()
            run_job(job)
        except Exception as e:
            print("[kali-remote] error:", e); time.sleep(2)

if __name__=="__main__":
    main()
