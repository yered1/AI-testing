from __future__ import annotations
import os, uuid, mimetypes
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from ..auth import get_principal
from ..tenancy import require_tenant
from ..settings import settings

router = APIRouter(prefix="/v2/artifacts", tags=["artifacts"])

def _root() -> str:
    root = getattr(settings, "EVIDENCE_DIR", None) or os.environ.get("EVIDENCE_DIR") or "./evidence"
    os.makedirs(root, exist_ok=True)
    return root

@router.post("/{run_id}")
async def upload_artifact(run_id: str, file: UploadFile = File(...), label: str = Form("evidence"), kind: str = Form("generic"), principal=Depends(require_tenant)) -> Dict[str, Any]:
    rid = str(uuid.uuid4())
    subdir = os.path.join(_root(), principal.tenant_id or "global", run_id)
    os.makedirs(subdir, exist_ok=True)
    stem, ext = os.path.splitext(file.filename or "")
    fname = f"{rid}{ext or ''}"
    dest = os.path.join(subdir, fname)
    data = await file.read()
    with open(dest, "wb") as fh:
        fh.write(data)
    meta = {
        "id": rid,
        "run_id": run_id,
        "label": label,
        "kind": kind,
        "filename": file.filename or fname,
        "stored_as": fname,
        "size": len(data),
        "content_type": file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    }
    # Optional: append to a simple JSONL catalog per run
    try:
        with open(os.path.join(subdir, "_catalog.jsonl"), "a", encoding="utf-8") as cat:
            import json
            cat.write(json.dumps(meta) + "\n")
    except Exception:
        pass
    return {"ok": True, "artifact": meta}

@router.get("/{run_id}")
def list_artifacts(run_id: str, principal=Depends(require_tenant)) -> Dict[str, Any]:
    subdir = os.path.join(_root(), principal.tenant_id or "global", run_id)
    artifacts: List[Dict[str, Any]] = []
    try:
        import json
        cat_path = os.path.join(subdir, "_catalog.jsonl")
        if os.path.exists(cat_path):
            with open(cat_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line: continue
                    try:
                        artifacts.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    return {"run_id": run_id, "artifacts": artifacts}

@router.get("/{run_id}/{artifact_id}")
def get_artifact(run_id: str, artifact_id: str, principal=Depends(require_tenant)):
    subdir = os.path.join(_root(), principal.tenant_id or "global", run_id)
    # find in catalog for metadata
    stored = None
    filename = None
    content_type = None
    import json
    cat_path = os.path.join(subdir, "_catalog.jsonl")
    if os.path.exists(cat_path):
        with open(cat_path, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("id") == artifact_id:
                    stored = obj.get("stored_as")
                    filename = obj.get("filename") or stored
                    content_type = obj.get("content_type") or "application/octet-stream"
                    break
    if not stored:
        # best-effort: guess by filename prefix
        for fn in os.listdir(subdir):
            if fn.startswith(artifact_id):
                stored = fn; filename = fn; break
    if not stored:
        raise HTTPException(status_code=404, detail="artifact not found")
    path = os.path.join(subdir, stored)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="file missing")
    return FileResponse(path, media_type=content_type or "application/octet-stream",
                        filename=filename or os.path.basename(path),
                        background=BackgroundTask(lambda: None))
