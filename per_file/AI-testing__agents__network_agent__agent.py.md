# File: AI-testing/agents/network_agent/agent.py

- Size: 4305 bytes
- Kind: text
- SHA256: 9b3545f2342aa6940a6747493b0707c9951f3b5515202d2466a9e4370b2848de

## Python Imports

```
json, os, requests, shlex, subprocess, time, uuid
```

## Head (first 60 lines)

```
import os, time, json, uuid, requests, subprocess, shlex

ORCH = os.environ.get("ORCH_URL","http://orchestrator:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"net-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN","")
ALLOW_ACTIVE = os.environ.get("ALLOW_ACTIVE_SCAN","0") in ("1","true","yes","on")

AGENT_ID=None
AGENT_KEY=None

def hdr():
    return {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY, "Content-Type":"application/json"}

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN: raise SystemExit("Missing AGENT_TOKEN")
    r = requests.post(f"{ORCH}/v2/agents/register", json={"enroll_token": ENROLL_TOKEN,"name": AGENT_NAME,"kind":"network"}, headers={"X-Tenant-Id":TENANT}, timeout=20)
    r.raise_for_status(); d=r.json(); AGENT_ID=d["agent_id"]; AGENT_KEY=d["agent_key"]

def run_cmd(cmd, timeout=14400):
    cp = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)
    return {"rc": cp.returncode, "stdout": cp.stdout[-20000:], "stderr": cp.stderr[-20000:]}

def adapter_nmap_tcp_full(params):
    cidrs = []
    if isinstance(params, dict): cidrs = params.get("cidrs") or []
    if not cidrs: return {"error":"no cidrs"}
    out = "nmap_tcp_full.gnmap"
    cmd = f"nmap -sS -sV -O -T3 -p- -oG {out} " + " ".join(cidrs)
    if not ALLOW_ACTIVE: return {"adapter":"nmap_tcp_full","command":cmd,"note":"dry-run (ALLOW_ACTIVE_SCAN=0)"}
    res = run_cmd(cmd, timeout=21600)
    info = {"adapter":"nmap_tcp_full","command":cmd,"exec":res}
    try:
        if os.path.exists(out):
            info.setdefault("artifacts",[]).append({"name":out,"size":os.path.getsize(out)})
            up = requests.post(f"{ORCH}/v2/jobs/{JOB_ID}/artifacts", headers=hdr(), files={"file": open(out,"rb")}, data={"label":"nmap_tcp_full"}, timeout=60)
            info["artifact_upload_rc"]=up.status_code
    except Exception as e:
        info["artifact_upload_error"]=str(e)
    return info

def adapter_nmap_udp_top_200(params):
    cidrs = []
    if isinstance(params, dict): cidrs = params.get("cidrs") or []
    if not cidrs: return {"error":"no cidrs"}
    out = "nmap_udp_top_200.gnmap"
    cmd = f"nmap -sU --top-ports 200 -T3 -oG {out} " + " ".join(cidrs)
    if not ALLOW_ACTIVE: return {"adapter":"nmap_udp_top_200","command":cmd,"note":"dry-run (ALLOW_ACTIVE_SCAN=0)"}
    res = run_cmd(cmd, timeout=21600)
    info = {"adapter":"nmap_udp_top_200","command":cmd,"exec":res}
    try:
        if os.path.exists(out):
            info.setdefault("artifacts",[]).append({"name":out,"size":os.path.getsize(out)})
            up = requests.post(f"{ORCH}/v2/jobs/{JOB_ID}/artifacts", headers=hdr(), files={"file": open(out,"rb")}, data={"label":"nmap_udp_top_200"}, timeout=60)
            info["artifact_upload_rc"]=up.status_code
    except Exception as e:
        info["artifact_upload_error"]=str(e)
    return info

```

## Tail (last 60 lines)

```
            info.setdefault("artifacts",[]).append({"name":out,"size":os.path.getsize(out)})
            up = requests.post(f"{ORCH}/v2/jobs/{JOB_ID}/artifacts", headers=hdr(), files={"file": open(out,"rb")}, data={"label":"nmap_tcp_full"}, timeout=60)
            info["artifact_upload_rc"]=up.status_code
    except Exception as e:
        info["artifact_upload_error"]=str(e)
    return info

def adapter_nmap_udp_top_200(params):
    cidrs = []
    if isinstance(params, dict): cidrs = params.get("cidrs") or []
    if not cidrs: return {"error":"no cidrs"}
    out = "nmap_udp_top_200.gnmap"
    cmd = f"nmap -sU --top-ports 200 -T3 -oG {out} " + " ".join(cidrs)
    if not ALLOW_ACTIVE: return {"adapter":"nmap_udp_top_200","command":cmd,"note":"dry-run (ALLOW_ACTIVE_SCAN=0)"}
    res = run_cmd(cmd, timeout=21600)
    info = {"adapter":"nmap_udp_top_200","command":cmd,"exec":res}
    try:
        if os.path.exists(out):
            info.setdefault("artifacts",[]).append({"name":out,"size":os.path.getsize(out)})
            up = requests.post(f"{ORCH}/v2/jobs/{JOB_ID}/artifacts", headers=hdr(), files={"file": open(out,"rb")}, data={"label":"nmap_udp_top_200"}, timeout=60)
            info["artifact_upload_rc"]=up.status_code
    except Exception as e:
        info["artifact_upload_error"]=str(e)
    return info

ADAPTERS = {
    "network_nmap_tcp_full": adapter_nmap_tcp_full,
    "network_nmap_udp_top_200": adapter_nmap_udp_top_200,
}

JOB_ID=None

def main():
    global JOB_ID
    register()
    idle=0
    while True:
        try:
            requests.post(f"{ORCH}/v2/agents/heartbeat", headers=hdr(), timeout=10)
            lr = requests.post(f"{ORCH}/v2/agents/lease2", headers=hdr(), json={"kinds":["network"]}, timeout=40)
            if lr.status_code == 204:
                idle+=1; time.sleep(2); continue
            lr.raise_for_status()
            job = lr.json(); JOB_ID=job.get("id")
            adapter = (job.get("adapter") or "").strip()
            params = job.get("params") or {}
            fn = ADAPTERS.get(adapter)
            if fn is None:
                result={"note":"adapter not supported", "adapter":adapter}
            else:
                result=fn(params)
            requests.post(f"{ORCH}/v2/jobs/{JOB_ID}/events", headers=hdr(), json={"type":"job.started","payload":{"adapter":adapter}}, timeout=20)
            time.sleep(0.2)
            requests.post(f"{ORCH}/v2/jobs/{JOB_ID}/complete", headers=hdr(), json={"status":"succeeded","result":result}, timeout=30)
        except Exception as e:
            print("[network-agent] error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
```

