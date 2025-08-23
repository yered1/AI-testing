# File: AI-testing/orchestrator/app.py

- Size: 7445 bytes
- Kind: text
- SHA256: 5686f74af8dc06694cc0dfe2d1893fc9d9a1cc66e3787ff4dee91d9cda9794f3

## Python Imports

```
app_v2, bootstrap_extras, contextlib, fastapi, json, logging, os, routers, secrets, uvicorn
```

## Head (first 60 lines)

```
"""
Main FastAPI application for AI Pentest Platform Orchestrator
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting AI Pentest Platform Orchestrator...")
    
    # Startup
    yield
    
    # Shutdown
    logger.info("Shutting down Orchestrator...")

# Create FastAPI app
app = FastAPI(
    title="AI Pentest Platform Orchestrator",
    description="LLM-Orchestrated Penetration Testing Platform",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "version": "2.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
```

## Tail (last 60 lines)

```
    }
    return {"id": run_id, "status": "started"}

@app.get("/v2/runs/{run_id}")
async def get_run(run_id: str):
    """Get run status"""
    if run_id in runs:
        return runs[run_id]
    return {"error": "Not found"}

# Try to import and mount additional routers
try:
    from routers import findings_v2
    app.include_router(findings_v2.router)
    logger.info("Mounted findings_v2 router")
except ImportError:
    logger.warning("Could not import findings_v2 router")

try:
    from routers import llm_controller
    app.include_router(llm_controller.router)
    logger.info("Mounted llm_controller router")
except ImportError:
    logger.warning("Could not import llm_controller router")

# Try to load app_v2 if it exists
try:
    from app_v2 import app as app_v2
    # Mount v2 routes
    app.mount("/v2", app_v2)
    logger.info("Mounted app_v2")
except ImportError:
    logger.info("app_v2 not found, using basic implementation")

# Try to load bootstrap_extras if it exists
try:
    from bootstrap_extras import bootstrap_extras
    bootstrap_extras(app)
    logger.info("Applied bootstrap extras")
except ImportError:
    logger.info("No bootstrap extras found")

# Exception handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
```

