from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from ..db import get_db
from ..auth import Principal
from ..tenancy import require_tenant
from fastapi import Depends
from fastapi.templating import Jinja2Templates
import os, uuid, json, httpx

router = APIRouter()
templates = Jinja2Templates(directory=str(os.path.join(os.path.dirname(__file__), "..", "ui", "templates")))

@router.get("/ui/code", response_class=HTMLResponse)
def code_home(request: Request, principal: Principal = Depends(require_tenant)):
    return templates.TemplateResponse("code_review.html", {"request": request, "tenant": principal.tenant_id})

# This uses existing APIs: create engagement(type=code) -> autoplan(pack) -> validate -> plan -> run
# Then prompt user to upload code package labeled 'code_package'
