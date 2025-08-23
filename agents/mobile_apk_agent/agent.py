
import os, time, json, uuid, requests, sys, tempfile, re
from typing import Dict, Any

ORCH = os.environ.get("ORCH_URL","http://orchestrator:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_NAME = os.environ.get("AGENT_NAME", f"mobile-apk-{uuid.uuid4().hex[:6]}")
ENROLL_TOKEN = os.environ.get("AGENT_TOKEN", "")

AGENT_ID = None
AGENT_KEY = None

def hdr():
    return {"X-Tenant-Id": TENANT, "X-Agent-Id": AGENT_ID, "X-Agent-Key": AGENT_KEY, "Content-Type":"application/json"}

def register():
    global AGENT_ID, AGENT_KEY
    if not ENROLL_TOKEN:
        print("[apk-agent] Missing AGENT_TOKEN", file=sys.stderr); sys.exit(2)
    r = requests.post(f"{ORCH}/v2/agents/register", json={
        "enroll_token": ENROLL_TOKEN,
        "name": AGENT_NAME,
        "kind": "mobile_apk"
    }, headers={"X-Tenant-Id": TENANT}, timeout=20)
    r.raise_for_status()
    data = r.json()
    AGENT_ID = data["agent_id"]
    AGENT_KEY = data["agent_key"]
    print(f"[apk-agent] registered id={AGENT_ID}")

def lease_job() -> Dict[str, Any] | None:
    # Prefer lease2 (with run_id)
    try:
        r = requests.post(f"{ORCH}/v2/agents/lease2", headers=hdr(), json={"kinds":["mobile_apk"]}, timeout=40)
        if r.status_code == 204:
            return None
        if r.ok:
            d = r.json()
            d["_lease2"]=True
            return d
    except Exception as e:
        pass
    # Fallback to legacy lease
    r = requests.post(f"{ORCH}/v2/agents/lease", headers=hdr(), json={"kinds":["mobile_apk"]}, timeout=40)
    if r.status_code == 204:
        return None
    r.raise_for_status()
    d = r.json()
    d["_lease2"]=False
    return d

def download_artifact(artifact_id: str, dest_path: str):
    url = f"{ORCH}/v2/artifacts/{artifact_id}/download"
    with requests.get(url, headers=hdr(), stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)

def list_artifacts(run_id: str):
    url = f"{ORCH}/v2/runs/{run_id}/artifacts/index.json"
    r = requests.get(url, headers=hdr(), timeout=30)
    if r.ok:
        try:
            return r.json().get("artifacts", [])
        except Exception:
            return []
    return []

def upload_artifact(job_id: str, path: str, label="apk_summary", kind="json"):
    files = {"file": (os.path.basename(path), open(path,"rb"))}
    data = {"label": label, "kind": kind}
    r = requests.post(f"{ORCH}/v2/jobs/{job_id}/artifacts", headers={"X-Tenant-Id":TENANT,"X-Agent-Id":AGENT_ID,"X-Agent-Key":AGENT_KEY}, files=files, data=data, timeout=60)
    try:
        r.raise_for_status()
    finally:
        files["file"][1].close()

def analyze_apk(apk_path: str) -> Dict[str, Any]:
    try:
        from androguard.core.bytecodes.apk import APK
    except Exception as e:
        return {"error":"androguard not installed", "detail": str(e)}
    try:
        a = APK(apk_path)
        info = {
            "file_name": os.path.basename(apk_path),
            "package": a.package,
            "version_name": a.get_version_name(),
            "version_code": a.get_version_code(),
            "min_sdk": a.get_min_sdk_version(),
            "target_sdk": a.get_target_sdk_version(),
            "permissions": sorted(set(a.get_permissions() or [])),
            "activities": sorted(a.get_activities() or []),
            "services": sorted(a.get_services() or []),
            "receivers": sorted(a.get_receivers() or []),
            "providers": sorted(a.get_providers() or []),
            "main_activity": a.get_main_activity(),
        }
        # Exported components heuristic
        exported = []
        for name in (a.get_activities() or []):
            if a.is_activity_exported(name):
                exported.append({"type":"activity","name":name})
        for name in (a.get_services() or []):
            if a.is_service_exported(name):
                exported.append({"type":"service","name":name})
        for name in (a.get_receivers() or []):
            if a.is_receiver_exported(name):
                exported.append({"type":"receiver","name":name})
        for name in (a.get_providers() or []):
            if a.is_provider_exported(name):
                exported.append({"type":"provider","name":name})
        info["exported_components"]=exported

        # Cleartext traffic flag (best effort)
        try:
            uses_clear = a.get_element('application','usesCleartextTraffic')
            info["uses_cleartext_traffic"] = bool(uses_clear and uses_clear.get('{http://schemas.android.com/apk/res/android}usesCleartextTraffic') in ("true","True","1"))
        except Exception:
            info["uses_cleartext_traffic"] = None

        # Simple string scan for URLs and secrets
        suspicious = []
        try:
            data = a.get_file("resources.arsc")  # just to touch
        except Exception:
            pass
        # crude scan in raw bytes
        raw = open(apk_path,"rb").read()
        urls = set(re.findall(rb'(https?://[A-Za-z0-9\-\._~:/\?#\[\]@!\$&\'\(\)\*\+,;=%]+)', raw[:5_000_000]))
        suspicious += [{"kind":"url","value":u.decode("utf-8","ignore")} for u in list(urls)[:50]]
        api_key = re.findall(rb'(?i)[A-Z0-9]{20,}', raw[:5_000_000])
        if api_key:
            suspicious += [{"kind":"token_like","value":k.decode("utf-8","ignore")} for k in list(set(api_key))[:20]]
        info["suspicious"] = suspicious

        return {"summary": info}
    except Exception as e:
        return {"error":"analysis_failed","detail":str(e)}

def run_job(job, lease_meta):
    job_id = job["id"]
    adapter = (job.get("adapter") or "").strip()
    params = job.get("params") or {}
    requests.post(f"{ORCH}/v2/jobs/{job_id}/events", headers=hdr(), json={"type":"job.started","payload":{"adapter":adapter}}, timeout=20)

    if adapter != "apk_static_default":
        # no-op
        result = {"note":"unsupported adapter for mobile_apk agent","adapter":adapter}
        requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", headers=hdr(), json={"status":"succeeded","result":result}, timeout=30)
        return

    artifact_id = None
    # Prefer explicit artifact_id param
    if isinstance(params, dict):
        artifact_id = params.get("artifact_id")

    # If not provided, use run context (lease2) to find APK labeled 'mobile_apk' or .apk
    if not artifact_id and lease_meta.get("_lease2") and lease_meta.get("run_id"):
        arts = list_artifacts(lease_meta["run_id"])
        for a in arts:
            name = (a.get("label") or "") + " " + (a.get("path") or "")
            if "mobile_apk" in name or (a.get("path") or "").endswith(".apk"):
                artifact_id = a.get("id")
                break

    if not artifact_id:
        result = {"error":"no APK artifact found; provide params.artifact_id or upload with label 'mobile_apk' before starting run"}
        requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", headers=hdr(), json={"status":"failed","result":result}, timeout=30)
        return

    with tempfile.TemporaryDirectory() as td:
        apk_path = os.path.join(td, "app.apk")
        try:
            download_artifact(artifact_id, apk_path)
        except Exception as e:
            result = {"error":"download_failed","detail":str(e)}
            requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", headers=hdr(), json={"status":"failed","result":result}, timeout=30)
            return

        analysis = analyze_apk(apk_path)

        # Save summary JSON and upload
        summ_path = os.path.join(td, "apk_summary.json")
        with open(summ_path,"w",encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)
        try:
            upload_artifact(job_id, summ_path, label="apk_summary", kind="json")
        except Exception as e:
            print("[apk-agent] failed to upload summary:", e)

        # Try to extract manifest XML if possible (best effort)
        try:
            from androguard.core.bytecodes.apk import APK
            a = APK(apk_path)
            xml = a.get_android_manifest_xml()
            if xml:
                man_path = os.path.join(td, "AndroidManifest.xml")
                with open(man_path,"w",encoding="utf-8") as f:
                    f.write(xml)
                try:
                    upload_artifact(job_id, man_path, label="android_manifest", kind="xml")
                except Exception as e:
                    print("[apk-agent] manifest upload failed:", e)
        except Exception:
            pass

        requests.post(f"{ORCH}/v2/jobs/{job_id}/complete", headers=hdr(), json={"status":"succeeded","result":analysis}, timeout=30)

def main():
    register()
    idle=0
    while True:
        try:
            requests.post(f"{ORCH}/v2/agents/heartbeat", headers=hdr(), timeout=10)
            lease = lease_job()
            if not lease:
                idle+=1; time.sleep(2); continue
            idle=0
            job = lease
            run_job(job, lease)
        except Exception as e:
            print("[apk-agent] error:", e)
            time.sleep(2)

if __name__ == "__main__":
    main()
