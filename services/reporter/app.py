from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pdfkit, tempfile

app = FastAPI(title="Reporter")

class RenderReq(BaseModel):
    html: str

@app.post("/render")
def render_pdf(req: RenderReq):
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdfkit.from_string(req.html, tmp.name)
            tmp.flush()
            data = open(tmp.name, "rb").read()
        return {"pdf": data.hex()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
