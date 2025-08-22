import tempfile, subprocess, os, json
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
import requests

app = FastAPI(title="Reporter")

class RenderIn(BaseModel):
    html: str | None = Field(default=None, description="Raw HTML to render")
    url: str | None = Field(default=None, description="URL to fetch and render")
    title: str | None = "Report"

@app.post("/render/pdf", response_class=Response)
def render_pdf(inp: RenderIn):
    if not (inp.html or inp.url):
        raise HTTPException(400, "Provide html or url")
    html = inp.html
    if inp.url:
        try:
            r = requests.get(inp.url, timeout=30)
            r.raise_for_status()
            html = r.text
        except Exception as e:
            raise HTTPException(400, f"Fetch failed: {e}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
        f.write(html.encode("utf-8"))
        src = f.name
    out = src.replace(".html",".pdf")
    try:
        cp = subprocess.run(["wkhtmltopdf", "--quiet", src, out], capture_output=True, text=True, timeout=60)
        if cp.returncode != 0:
            raise HTTPException(500, f"wkhtmltopdf failed: {cp.stderr[-500:]}")
        data = open(out, "rb").read()
        return Response(content=data, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{(inp.title or "report")}.pdf"'})
    finally:
        for p in (src, out):
            try:
                os.remove(p)
            except Exception:
                pass
