# File: AI-testing/orchestrator/agent_sdk/http.py

- Size: 2303 bytes
- Kind: text
- SHA256: 65f9778a43b169ea0ea1731ac929dfd51f14e3a72aeaff26c1ea1c12cd58038d

## Python Imports

```
os, requests, time
```

## Head (first 60 lines)

```

import os, time, requests

class AgentClient:
    def __init__(self, base=None, tenant=None, agent_id=None, agent_key=None):
        self.base = (base or os.environ.get("ORCH_URL","http://localhost:8080")).rstrip("/")
        self.tenant = tenant or os.environ.get("TENANT_ID","t_demo")
        self.agent_id = agent_id or os.environ.get("X_AGENT_ID")
        self.agent_key = agent_key or os.environ.get("X_AGENT_KEY")

    def hdr(self):
        h = {"X-Tenant-Id": self.tenant, "Content-Type": "application/json"}
        if self.agent_id: h["X-Agent-Id"]=self.agent_id
        if self.agent_key: h["X-Agent-Key"]=self.agent_key
        return h

    def register(self, enroll_token, name, kind):
        r = requests.post(self.base+"/v2/agents/register", headers={"X-Tenant-Id": self.tenant, "Content-Type":"application/json"},
                          json={"enroll_token": enroll_token, "name": name, "kind": kind}, timeout=20)
        r.raise_for_status()
        data = r.json()
        self.agent_id = data.get("agent_id")
        self.agent_key = data.get("agent_key")
        return data

    def heartbeat(self):
        return requests.post(self.base+"/v2/agents/heartbeat", headers=self.hdr(), timeout=10)

    def lease2(self, kinds):
        r = requests.post(self.base+"/v2/agents/lease2", headers=self.hdr(), json={"kinds": kinds}, timeout=40)
        return r

    def lease(self, kinds):
        r = requests.post(self.base+"/v2/agents/lease", headers=self.hdr(), json={"kinds": kinds}, timeout=40)
        return r

    def job_event(self, job_id, typ, payload):
        return requests.post(self.base+f"/v2/jobs/{job_id}/events", headers=self.hdr(), json={"type": typ, "payload": payload}, timeout=20)

    def job_complete(self, job_id, status, result):
        return requests.post(self.base+f"/v2/jobs/{job_id}/complete", headers=self.hdr(), json={"status": status, "result": result}, timeout=40)

    def upload_artifact(self, job_id, filepath, label=None):
        files = {"file": open(filepath, "rb")}
        data = {"label": label} if label else {}
        h = self.hdr(); h.pop("Content-Type", None)
        r = requests.post(self.base+f"/v2/jobs/{job_id}/artifacts", headers=h, data=data, files=files, timeout=120)
        r.raise_for_status()
        return r.json()
```

