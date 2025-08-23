
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os, json, requests

router = APIRouter()

APP_ROOT = os.path.dirname(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(APP_ROOT, "ui", "templates")
STATIC_DIR = os.path.join(APP_ROOT, "ui", "static")
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape())

def _hdr(request: Request):
    # Pass-through identity headers (dev or OIDC proxy)
    h = {
        "Content-Type":"application/json",
        "X-Dev-User": request.headers.get("X-Dev-User","ui"),
        "X-Dev-Email": request.headers.get("X-Dev-Email","ui@example.com"),
        "X-Tenant-Id": request.headers.get("X-Tenant-Id","t_demo"),
    }
    return h

@router.get("/ui/mobile", response_class=HTMLResponse)
def mobile_home(request: Request):
    tmpl = env.get_template("mobile_review.html")
    return tmpl.render(title="Mobile Review", request=request)

# helper: upload artifact to a run
@router.post("/ui/mobile/upload")
async def mobile_upload(request: Request, run_id: str = Form(...), file: UploadFile = File(...)):
    url = f"http://localhost:8080/v2/runs/{run_id}/artifacts"
    files = {"file": (file.filename, await file.read(), file.content_type or "application/octet-stream")}
    data = {"label":"mobile_apk","kind":"apk"}
    r = requests.post(url, headers={"X-Dev-User": request.headers.get("X-Dev-User","ui"),
                                    "X-Dev-Email": request.headers.get("X-Dev-Email","ui@example.com"),
                                    "X-Tenant-Id": request.headers.get("X-Tenant-Id","t_demo")}, files=files, data=data, timeout=120)
    r.raise_for_status()
    return {"ok": True}

