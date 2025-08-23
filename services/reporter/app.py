import os
import tempfile
import subprocess
from typing import Optional
from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import Response, JSONResponse

app = FastAPI(title="Reporter (hardened)")

ALLOW_REMOTE_URLS = os.environ.get("ALLOW_REMOTE_URLS", "0") in {"1","true","True"}
WKHTMLTOPDF = os.environ.get("WKHTMLTOPDF_PATH", "wkhtmltopdf")

def _run_wkhtmltopdf(input_html: str) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        html_path = os.path.join(td, "doc.html")
        pdf_path = os.path.join(td, "doc.pdf")
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write(input_html)
        try:
            subprocess.run([WKHTMLTOPDF, "--quiet", html_path, pdf_path], check=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"wkhtmltopdf failed: {e}")
        with open(pdf_path, "rb") as fh:
            return fh.read()

def _render(html: Optional[str], url: Optional[str]) -> bytes:
    if url and not ALLOW_REMOTE_URLS:
        raise HTTPException(status_code=400, detail="URL rendering disabled; submit HTML instead")
    if not html:
        raise HTTPException(status_code=400, detail="Missing 'html'")
    return _run_wkhtmltopdf(html)

def _resp(pdf: bytes):
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": "inline; filename=report.pdf"})

@app.post("/render")
def render_default(html: Optional[str] = Body(None), url: Optional[str] = Body(None)):
    return _resp(_render(html, url))

@app.get("/healthz")
def healthz():
    return JSONResponse({"ok": True})
