# File: AI-testing/orchestrator/routers/ui_builder.py

- Size: 717 bytes
- Kind: text
- SHA256: 81f0f233b01781689bce2c5b9bd991539e1fcbd06141b2dac2d33d84f1b4a2cb

## Python Imports

```
fastapi, pathlib
```

## Head (first 60 lines)

```

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pathlib

router = APIRouter()
BASE = pathlib.Path(__file__).resolve().parents[1] / "ui"
templates = Jinja2Templates(directory=str(BASE / "templates"))

# mount static only if not already mounted by ui_pages
def mount_static(app):
    try:
        app.mount("/ui/static", StaticFiles(directory=str(BASE / "static")), name="ui_static")
    except Exception:
        pass

@router.get("/ui/builder", response_class=HTMLResponse)
def ui_builder(request: Request):
    return templates.TemplateResponse("builder.html", {"request": request})
```

