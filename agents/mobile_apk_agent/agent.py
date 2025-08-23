import os, re, io, json, zipfile, tempfile, hashlib, requests
from typing import Dict, Any, List, Optional

ORCH = os.environ.get("ORCH_URL", "http://localhost:8000")
ORCH_TOKEN = os.environ.get("ORCH_TOKEN", "")

def hdr(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if ORCH_TOKEN:
        h["Authorization"] = f"Bearer {ORCH_TOKEN}"
    if extra:
        h.update(extra)
    return h

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def list_apk(apk_path: str) -> List[str]:
    with zipfile.ZipFile(apk_path, "r") as z:
        return z.namelist()

def analyze_apk(apk_path: str) -> Dict[str, Any]:
    """Static APK inspection without external deps (heuristic)."""
    try:
        info: Dict[str, Any] = {"apk_path": apk_path, "sha256": sha256_file(apk_path)}
        names = list_apk(apk_path)
        info["files"] = names[:200]  # cap for brevity
        suspicious: List[Dict[str, str]] = []

        # Read a window of bytes for string scanning
        with open(apk_path, "rb") as fh:
            raw = fh.read(5_000_000)

        # URLs
        try:
            urls = re.findall(rb'(https?://[A-Za-z0-9\-\._~:/\?#\[\]@!\$&\'\(\)\*\+,;=%]+)', raw)
            suspicious += [{"kind": "url", "value": u.decode("utf-8", "ignore")} for u in list(dict.fromkeys(urls))[:100]]
        except Exception:
            pass

        # Token-like
        try:
            keys = re.findall(rb'(?i)[A-Z0-9]{20,}', raw)
            suspicious += [{"kind": "token_like", "value": k.decode("utf-8", "ignore")} for k in list(dict.fromkeys(keys))[:50]]
        except Exception:
            pass

        info["suspicious"] = suspicious
        return {"summary": info}
    except Exception as e:
        return {"error": "analysis_failed", "detail": str(e)}

def _post_event(job_id: str, type_: str, payload: Dict[str, Any]) -> None:
    try:
        requests.post(f"{ORCH}/v2/jobs/{job_id}/events", headers=hdr(), json={"type": type_, "payload": payload}, timeout=20)
    except Exception:
        # best-effort
        pass

def _download(url: str) -> str:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    fd, path = tempfile.mkstemp(prefix="apk_", suffix=".apk")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(r.content)
    return path

def run_job(job: Dict[str, Any], lease_meta: Dict[str, Any]) -> None:
    job_id = job.get("id") or ""
    adapter = (job.get("adapter") or "").strip()
    params: Dict[str, Any] = job.get("params") or {}

    _post_event(job_id, "job.started", {"adapter": adapter})

    if adapter != "apk_static_default":
        _post_event(job_id, "job.finished", {"status": "skipped", "reason": "unsupported_adapter"})
        return

    apk_path = params.get("apk_path")
    apk_url = params.get("apk_url")
    temp_path: Optional[str] = None

    try:
        if not apk_path and apk_url:
            temp_path = _download(apk_url)
            apk_path = temp_path
        if not apk_path or not os.path.exists(apk_path):
            raise FileNotFoundError("apk_path missing or not found")

        result = analyze_apk(apk_path)
        status = "ok" if "summary" in result else "error"
        _post_event(job_id, "job.finished", {"status": status, "result": result})
    except Exception as e:
        _post_event(job_id, "job.finished", {"status": "error", "error": str(e)})
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

if __name__ == "__main__":
    # Simple manual test harness (optional)
    import sys
    if len(sys.argv) == 2:
        print(json.dumps(analyze_apk(sys.argv[1]), indent=2))
    else:
        print("Usage: python agent.py /path/to/app.apk")
