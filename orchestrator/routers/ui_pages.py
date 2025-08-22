from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.templating import Jinja2Templates

router = APIRouter()

BASE = Path(__file__).resolve().parents[1] / "ui"
TEMPLATES_DIR = BASE / "templates"
STATIC_DIR = BASE / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
# Static will be mounted by app_v2 or bootstrap when include happens (we export a Starlette app)
# But since we don't have app here, we expose a helper for the caller:
def mount_static(app):
    if not any(isinstance(r.app, StaticFiles) and getattr(r, 'path', '') == '/ui/static' for r in getattr(app, 'routes', [])):
        app.mount('/ui/static', StaticFiles(directory=str(STATIC_DIR)), name='ui_static')

@router.get('/ui', response_class=HTMLResponse)
def ui_home(request: Request):
    return templates.TemplateResponse('home.html', {'request': request})

@router.get('/ui/new', response_class=HTMLResponse)
def ui_new_eng(request: Request):
    return templates.TemplateResponse('new_engagement.html', {'request': request})

@router.get('/ui/runs/{run_id}', response_class=HTMLResponse)
def ui_run_detail(run_id: str, request: Request):
    return templates.TemplateResponse('run_detail.html', {'request': request, 'run_id': run_id})

@router.get('/ui/admin', response_class=HTMLResponse)
def ui_admin(request: Request):
    return templates.TemplateResponse('admin.html', {'request': request})
