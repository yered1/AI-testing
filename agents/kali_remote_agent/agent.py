
import os, time, uuid, base64, tempfile, json, sys, traceback
from pathlib import Path
import paramiko, requests

from orchestrator.agent_sdk.http import AgentClient  # if installed as package path differs, we'll vendor simple fallback

ORCH = os.environ.get("ORCH_URL","http://localhost:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"kali-remote-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN", "")
ALLOW_ACTIVE = os.environ.get("ALLOW_ACTIVE_SCAN","0") in ("1","true","yes","on")

SSH_HOST = os.environ.get("SSH_HOST","")
SSH_PORT = int(os.environ.get("SSH_PORT","22"))
SSH_USER = os.environ.get("SSH_USER","")
SSH_KEY_B64 = os.environ.get("SSH_KEY_BASE64","")
SSH_PASSWORD = os.environ.get("SSH_PASSWORD","")

TOOLS_YAML = os.environ.get("TOOLS_YAML","/app/agent/tools.yaml")

client = AgentClient(base=ORCH, tenant=TENANT)

def load_tools():
    try:
        import yaml
    except Exception:
        return {}
    try:
        return yaml.safe_load(open(TOOLS_YAML, "r"))
    except Exception:
        return {}

def ssh_connect():
    key = None
    if SSH_KEY_B64:
        kdata = base64.b64decode(SSH_KEY_B64.encode("utf-8"))
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(kdata); tmp.close()
        key = paramiko.RSAKey.from_private_key_file(tmp.name)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if key:
            ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, pkey=key, timeout=20)
        else:
            ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD, timeout=20)
    except Exception as e:
        raise
    sftp = ssh.open_sftp()
    return ssh, sftp

def run_remote(cmd, timeout=3600):
    ssh, sftp = ssh_connect()
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
        out = stdout.read().decode("utf-8","ignore")[-200000:]
        err = stderr.read().decode("utf-8","ignore")[-200000:]
        rc = stdout.channel.recv_exit_status()
        return {"rc": rc, "stdout": out, "stderr": err}
    finally:
        try: sftp.close()
        except: pass
        try: ssh.close()
        except: pass

def adapter_run_tool(params):
    """Generic tool runner with allowlist from tools.yaml (template + args)."""
    tools = load_tools()
    name = (params or {}).get("name")
    args = (params or {}).get("args", "")
    tpl = (tools.get("tools",{}).get(name) or {}).get("cmd")
    if not tpl:
        return {"error": f"tool '{name}' not allowed or missing"}
    if ("nmap" in name or "sqlmap" in name or "ffuf" in name) and not ALLOW_ACTIVE:
        return {"note":"dry-run (ALLOW_ACTIVE_SCAN=0)","cmd": tpl.replace("{args}", str(args))}
    cmd = tpl.replace("{args}", str(args))
    res = run_remote(cmd)
    return {"adapter":"run_tool","tool": name, "command": cmd, "result": res}

def adapter_nmap_tcp_top_1000(params):
    target = None
    if isinstance(params, dict):
        for k in ("target","ip","host"): 
            if params.get(k): target = params[k]; break
    if not target:
        return {"error":"missing target"}
    cmd = f"nmap -Pn --top-ports 1000 -T3 {target}"
    if not ALLOW_ACTIVE:
        return {"note":"dry-run (ALLOW_ACTIVE_SCAN=0)","command":cmd}
    res = run_remote(cmd)
    return {"adapter":"nmap_tcp_top_1000","command":cmd,"result":res}

ADAPTERS = {
    "run_tool": adapter_run_tool,
    "nmap_tcp_top_1000": adapter_nmap_tcp_top_1000,
}

def main():
    if not ENROLL_TOKEN:
        print("[kali-remote] Missing AGENT_TOKEN", file=sys.stderr); sys.exit(2)
    reg = client.register(ENROLL_TOKEN, AGENT_NAME, "kali_remote")
    print("[kali-remote] registered id=", reg.get("agent_id"))
    idle = 0
    while True:
        try:
            client.heartbeat()
            lr = client.lease2(["kali_remote"])
            if lr.status_code == 204:
                time.sleep(2); continue
            if lr.status_code >= 400:
                # fallback
                lr = client.lease(["kali_remote"])
                if lr.status_code == 204:
                    time.sleep(2); continue
            job = lr.json()
            job_id = job["id"]
            adapter = (job.get("adapter") or "").strip()
            params = job.get("params") or {}
            fn = ADAPTERS.get(adapter)
            if fn is None:
                result = {"adapter": adapter or "unknown", "params": params, "note": "no adapter implemented for kali-remote"}
            else:
                result = fn(params)
            client.job_event(job_id, "job.started", {"adapter": adapter})
            client.job_complete(job_id, "succeeded", result)
        except Exception as e:
            tb = traceback.format_exc()
            try:
                client.job_event(job_id, "job.error", {"error": str(e), "trace": tb})
            except Exception:
                pass
            time.sleep(3)

if __name__ == "__main__":
    main()
