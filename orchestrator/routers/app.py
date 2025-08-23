# Destination: patches/v2.0.0/orchestrator/routers/app.py
# Rationale: Single source of truth for the FastAPI application
# Consolidates all routers and middleware in one place

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

# Import all routers
from . import (
    v2_agents_bus,
    v2_agents_bus_lease2,
    v2_artifacts,
    v2_artifacts_index,
    v2_artifacts_downloads,
    findings_v2,
    v2_findings_reports,
    v2_quotas_approvals,
    v2_listings,
    v2_brain,
    v3_brain,
    v3_brain_guarded,
    ui_pages,
    ui_brain,
    ui_code,
    ui_builder,
    ui_mobile
)

# Import database and models
from ..db import engine, Base
from ..models import user, tenant, engagement, plan, run, job, agent, artifact, finding

logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifecycle events."""
    # Startup
    logger.info("Starting orchestrator application...")
    
    # Create database tables if they don't exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    
    # Initialize any background tasks or connections
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down orchestrator application...")
    # Cleanup connections, background tasks, etc.
    logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="AI Testing Orchestrator",
    description="Security testing orchestration platform with AI-powered planning",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
allowed_hosts = os.getenv("ALLOWED_HOSTS", "*").split(",")
if allowed_hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# Mount static files if UI directory exists
ui_path = Path(__file__).parent.parent / "ui" / "dist"
if ui_path.exists():
    app.mount("/ui", StaticFiles(directory=str(ui_path), html=True), name="ui")
    logger.info(f"Mounted UI static files from {ui_path}")

# Evidence/artifacts directory
evidence_dir = os.getenv("EVIDENCE_DIR", "/evidence")
if os.path.exists(evidence_dir):
    app.mount("/evidence", StaticFiles(directory=evidence_dir), name="evidence")
    logger.info(f"Mounted evidence directory: {evidence_dir}")

# Health check endpoint (root level)
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Testing Orchestrator",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Include v2 routers
app.include_router(v2_agents_bus.router, prefix="/v2", tags=["agents"])
app.include_router(v2_agents_bus_lease2.router, prefix="/v2", tags=["agents"])
app.include_router(v2_artifacts.router, prefix="/v2", tags=["artifacts"])
app.include_router(v2_artifacts_index.router, prefix="/v2", tags=["artifacts"])
app.include_router(v2_artifacts_downloads.router, prefix="/v2", tags=["artifacts"])
app.include_router(findings_v2.router, prefix="/v2", tags=["findings"])
app.include_router(v2_findings_reports.router, prefix="/v2", tags=["reports"])
app.include_router(v2_quotas_approvals.router, prefix="/v2", tags=["quotas"])
app.include_router(v2_listings.router, prefix="/v2", tags=["listings"])
app.include_router(v2_brain.router, prefix="/v2", tags=["brain"])

# Include v3 routers
app.include_router(v3_brain.router, prefix="/v3", tags=["brain"])
app.include_router(v3_brain_guarded.router, prefix="/v3", tags=["brain"])

# Include UI routers
app.include_router(ui_pages.router, tags=["ui"])
app.include_router(ui_brain.router, prefix="/ui", tags=["ui"])
app.include_router(ui_code.router, prefix="/ui", tags=["ui"])
app.include_router(ui_builder.router, prefix="/ui", tags=["ui"])
app.include_router(ui_mobile.router, prefix="/ui", tags=["ui"])

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "path": str(request.url.path)}
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.error(f"Server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# Middleware for logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"{request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Service"] = "orchestrator"
    
    return response

# Import additional utilities
from datetime import datetime
from fastapi.responses import JSONResponse
import time

logger.info("Orchestrator application initialized with all routers")