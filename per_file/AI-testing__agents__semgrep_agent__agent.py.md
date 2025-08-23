# File: AI-testing/agents/semgrep_agent/agent.py

- Size: 7080 bytes
- Kind: text
- SHA256: 6289c055919e105bc76153f95bf494c98ddec870fc4621b33206f6dacf921f22

## Python Imports

```
json, os, pathlib, requests, shlex, subprocess, sys, tarfile, tempfile, time, uuid, zipfile
```

## Head (first 60 lines)

```
import os, time, json, uuid, requests, tempfile, subprocess, shlex, sys, tarfile, zipfile, pathlib

ORCH = os.environ.get("ORCH_URL","http://localhost:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"semgrep-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN", "")

AGENT_ID = None
AGENT_KEY = None

def hdr():
    return {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY, "Content-Type":"application/json"}

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN:
        print("[semgrep-agent] Missing AGENT_TOKEN", file=sys.stderr); sys.exit(2)
    r = requests.post(f"{ORCH}/v2/agents/register", json={
        "enroll_token": ENROLL_TOKEN,
        "name": AGENT_NAME,
        "kind": "semgrep"
    }, headers={"X-Tenant-Id": TENANT}, timeout=20)
    r.raise_for_status()
    data = r.json()
    AGENT_ID = data["agent_id"]
    AGENT_KEY = data["agent_key"]
    print(f"[semgrep-agent] registered id={AGENT_ID}")

def run_cmd(cmd: str, timeout=7200):
    try:
        print("[semgrep-agent] running:", cmd)
        cp = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)
        return {"rc": cp.returncode, "stdout": cp.stdout[-20000:], "stderr": cp.stderr[-20000:]}
    except Exception as e:
        return {"rc": -1, "error": str(e)}

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def download_artifact(artifact_id, out_path):
    url = f"{ORCH}/v2/artifacts/{artifact_id}/download"
    r = requests.get(url, headers=hdr(), timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"download {artifact_id} failed: {r.status_code} {r.text[:200]}")
    with open(out_path, "wb") as f:
        f.write(r.content)
    return out_path

def extract_archive(archive_path, workdir):
    ext = archive_path.lower()
    if ext.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as z:
            z.extractall(workdir)
    elif ext.endswith(".tar.gz") or ext.endswith(".tgz"):
        with tarfile.open(archive_path, "r:gz") as t:
            t.extractall(workdir)
    elif ext.endswith(".tar"):
        with tarfile.open(archive_path, "r:") as t:
            t.extractall(workdir)
    else:
```

## Tail (last 60 lines)

```
            path = r.get("path")
            cwe = r.get("extra",{}).get("metadata",{}).get("cwe")
            finding = {
                "title": title,
                "severity": sev,
                "description": msg,
                "assets": {"path": path, "start": r.get("start"), "end": r.get("end"), "cwe": cwe},
                "tags": {"tool":"semgrep","rule": r.get("check_id")}
            }
            findings.append(finding)
    except Exception as e:
        findings = [{"title":"Semgrep run issue","severity":"info","description":str(e)}]
    # upload artifact
    files = {"file": ("semgrep.json","".join(open(out_json,"r",errors="ignore").readlines()[-100000:]).encode("utf-8"),"application/json") if os.path.exists(out_json) else ("semgrep.txt", json.dumps(exec_res).encode("utf-8"), "text/plain")}
    requests.post(f"{ORCH}/v2/jobs/{job['id']}/artifacts", headers=hdr(), data={"label":"semgrep_results","kind":"sast"}, files=files, timeout=60)
    # upsert findings
    requests.post(f"{ORCH}/v2/runs/{run_id}/findings", headers={"X-Tenant-Id": TENANT, "Content-Type":"application/json"}, json=findings, timeout=60)
    return {"exec": exec_res, "findings_count": len(findings)}

ADAPTERS = {"semgrep_default": adapter_semgrep_default}

def main():
    register()
    lease2_supported = True
    while True:
        try:
            requests.post(f"{ORCH}/v2/agents/heartbeat", headers=hdr(), timeout=10)
            lr = requests.post(f"{ORCH}/v2/agents/lease2", headers=hdr(), json={"kinds":["semgrep"]}, timeout=40)
            if lr.status_code == 404:
                lease2_supported = False
            if lr.status_code == 204:
                time.sleep(2); continue
            if lr.status_code == 200:
                job = lr.json()
                lease_payload = job
            else:
                if not lease2_supported:
                    lr = requests.post(f"{ORCH}/v2/agents/lease", headers=hdr(), json={"kinds":["semgrep"]}, timeout=40)
                    if lr.status_code == 204: time.sleep(2); continue
                    lr.raise_for_status()
                    job = lr.json()
                    # need run_id; try to infer none
                    lease_payload = {}
                else:
                    lr.raise_for_status()
                    continue
            adapter = (job.get("adapter") or "").strip()
            fn = ADAPTERS.get(adapter)
            if fn is None:
                result = {"note":"adapter not supported", "adapter":adapter}
            else:
                result = fn(job, lease_payload)
            requests.post(f"{ORCH}/v2/jobs/{job['id']}/events", headers=hdr(), json={"type":"job.started","payload":{"adapter": adapter}}, timeout=20)
            requests.post(f"{ORCH}/v2/jobs/{job['id']}/complete", headers=hdr(), json={"status":"succeeded","result":result}, timeout=30)
        except Exception as e:
            print("[semgrep-agent] error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
```

