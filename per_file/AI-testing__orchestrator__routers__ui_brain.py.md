# File: AI-testing/orchestrator/routers/ui_brain.py

- Size: 813 bytes
- Kind: text
- SHA256: 1363edbf3a0de39c51b0e6dc20190554718639f67e10d468e3f2ae8a019351e2

## Python Imports

```
fastapi, os
```

## Head (first 60 lines)

```
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

router = APIRouter()
_base = os.path.dirname(os.path.dirname(__file__))
_tmpl = os.path.join(_base, "ui", "templates")
_stat = os.path.join(_base, "ui", "static")
templates = Jinja2Templates(directory=_tmpl)

def ensure_static_mount(app):
    already = any(getattr(r, 'path', '') == "/ui/static" for r in app.routes)
    if not already:
        app.mount("/ui/static", StaticFiles(directory=_stat), name="ui_static")

@router.get("/ui/brain", response_class=HTMLResponse)
async def ui_brain(request: Request):
    ensure_static_mount(request.app)
    return templates.TemplateResponse("brain_builder.html", {"request": request})
```

