"""AI-Testing Platform Orchestrator"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="AI-Testing Platform",
    version="2.0.0",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": "AI-Testing Platform",
        "version": "2.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v2/catalog")
async def get_catalog():
    return {
        "tests": [
            {"id": "web_scan", "name": "Web Security Scan"},
            {"id": "network_scan", "name": "Network Scan"},
            {"id": "code_analysis", "name": "Code Analysis"}
        ]
    }

# Import routers that actually work
try:
    from routers.engagements import router as engagements_router
    app.include_router(engagements_router, prefix="/api/v2/engagements")
except ImportError:
    pass

try:
    from routers.agents import router as agents_router
    app.include_router(agents_router, prefix="/api/v2/agents")
except ImportError:
    pass
