# File: AI-testing/agents/zap_auth_agent/agent.py

- Size: 4533 bytes
- Kind: text
- SHA256: a98dbdfddf848f094aa0d9252738e54277fc6b7f72b860830d37e663c265c74d

## Python Imports

```
json, os, requests, shlex, subprocess, tempfile, time, uuid, zapv2
```

## Head (first 60 lines)

```
import os, time, json, uuid, requests, subprocess, shlex, tempfile

ORCH = os.environ.get("ORCH_URL","http://orchestrator:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"zapauth-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN","")
ALLOW_ACTIVE = os.environ.get("ALLOW_ACTIVE_SCAN","0") in ("1","true","yes","on")
ZAP_PORT = int(os.environ.get("ZAP_PORT","8090"))

AGENT_ID=None
AGENT_KEY=None
JOB_ID=None

def hdr():
    return {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY, "Content-Type":"application/json"}

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN: raise SystemExit("Missing AGENT_TOKEN")
    r = requests.post(f"{ORCH}/v2/agents/register", json={"enroll_token": ENROLL_TOKEN,"name": AGENT_NAME,"kind":"zap_auth"}, headers={"X-Tenant-Id":TENANT}, timeout=20)
    r.raise_for_status(); d=r.json(); AGENT_ID=d["agent_id"]; AGENT_KEY=d["agent_key"]

def run(cmd, timeout=7200):
    return subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)

def adapter_zap_auth_full(params):
    target = (params.get("target") or "").strip()
    login_url = (params.get("login_url") or target).strip()
    user_field = params.get("user_field","username")
    pass_field = params.get("pass_field","password")
    username = params.get("username","")
    password = params.get("password","")
    context_name = "ctx"
    if not target:
        return {"error":"target required"}
    if not ALLOW_ACTIVE:
        return {"adapter":"zap_auth_full","note":"dry-run (ALLOW_ACTIVE_SCAN=0)","target":target,"login_url":login_url,
                "user_field":user_field,"pass_field":pass_field,"username":bool(username),"password":bool(password)}
    # Start daemon
    z = run(f"zap.sh -daemon -port {ZAP_PORT} -config api.disablekey=true")
    time.sleep(5)
    from zapv2 import ZAPv2
    zap = ZAPv2(proxies={'http': f'http://127.0.0.1:{ZAP_PORT}', 'https': f'http://127.0.0.1:{ZAP_PORT}'})
    res = {}
    # Create context + include target
    ctxid = zap.context.new_context(context_name)
    zap.context.include_in_context(context_name, f"{target}.*")
    # Form-based authentication
    zap.authentication.set_authentication_method(ctxid, "formBasedAuthentication",
        f"loginUrl={login_url}&loginRequestData={user_field}={{%username%}}&{pass_field}={{%password%}}")
    uid = zap.users.new_user(ctxid, "user1")
    zap.users.set_user_credentials(ctxid, uid, f"username={username}&password={password}")
    zap.users.set_user_enabled(ctxid, uid, "true")
    # Spider as user, then active scan
    zap.spider.scan_as_user(ctxid, uid, target)
    time.sleep(10)
    zap.ascan.scan_as_user(ctxid, uid, target)
    # Wait a bit and export report
    time.sleep(30)
    html="zap_auth_report.html"
```

## Tail (last 60 lines)

```
    z = run(f"zap.sh -daemon -port {ZAP_PORT} -config api.disablekey=true")
    time.sleep(5)
    from zapv2 import ZAPv2
    zap = ZAPv2(proxies={'http': f'http://127.0.0.1:{ZAP_PORT}', 'https': f'http://127.0.0.1:{ZAP_PORT}'})
    res = {}
    # Create context + include target
    ctxid = zap.context.new_context(context_name)
    zap.context.include_in_context(context_name, f"{target}.*")
    # Form-based authentication
    zap.authentication.set_authentication_method(ctxid, "formBasedAuthentication",
        f"loginUrl={login_url}&loginRequestData={user_field}={{%username%}}&{pass_field}={{%password%}}")
    uid = zap.users.new_user(ctxid, "user1")
    zap.users.set_user_credentials(ctxid, uid, f"username={username}&password={password}")
    zap.users.set_user_enabled(ctxid, uid, "true")
    # Spider as user, then active scan
    zap.spider.scan_as_user(ctxid, uid, target)
    time.sleep(10)
    zap.ascan.scan_as_user(ctxid, uid, target)
    # Wait a bit and export report
    time.sleep(30)
    html="zap_auth_report.html"
    run(f"zap.sh -cmd -port {ZAP_PORT} -quickout {html}")
    out={"adapter":"zap_auth_full","report":html}
    try:
        if os.path.exists(html):
            up = requests.post(f"{ORCH}/v2/jobs/{JOB_ID}/artifacts", headers=hdr(), files={"file": open(html,"rb")}, data={"label":"zap_auth_report"}, timeout=60)
            out["artifact_upload_rc"]=up.status_code
    except Exception as e:
        out["artifact_upload_error"]=str(e)
    return out

ADAPTERS={"web_zap_auth_full": adapter_zap_auth_full}

def main():
    global JOB_ID
    register()
    while True:
        try:
            requests.post(f"{ORCH}/v2/agents/heartbeat", headers=hdr(), timeout=10)
            lr = requests.post(f"{ORCH}/v2/agents/lease2", headers=hdr(), json={"kinds":["zap_auth"]}, timeout=40)
            if lr.status_code == 204:
                time.sleep(2); continue
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
            print("[zap-auth-agent] error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
```

