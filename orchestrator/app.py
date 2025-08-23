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
        "service": "AI Pentest Platform Orchestrator",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

# V1 Catalog endpoints (basic implementation)
@app.get("/v1/catalog")
async def get_catalog():
    """Get test catalog"""
    try:
        import json
        catalog_path = "/app/catalog/tests/tests.json"
        if os.path.exists(catalog_path):
            with open(catalog_path, 'r') as f:
                tests = json.load(f)
        else:
            tests = {
                "network_scan": {
                    "id": "network_scan",
                    "name": "Network Scan",
                    "description": "Basic network scanning",
                    "category": "Network"
                }
            }
        
        return {
            "tests": tests,
            "count": len(tests)
        }
    except Exception as e:
        logger.error(f"Error loading catalog: {e}")
        return {"tests": {}, "count": 0}

@app.get("/v1/catalog/packs")
async def get_packs():
    """Get test packs"""
    try:
        import json
        packs_path = "/app/catalog/packs/packs.json"
        if os.path.exists(packs_path):
            with open(packs_path, 'r') as f:
                packs = json.load(f)
        else:
            packs = {
                "basic": {
                    "id": "basic",
                    "name": "Basic Pack",
                    "tests": ["network_scan"]
                }
            }
        
        return {
            "packs": packs,
            "count": len(packs)
        }
    except Exception as e:
        logger.error(f"Error loading packs: {e}")
        return {"packs": {}, "count": 0}

# V2 Agent endpoints (basic implementation)
agents_store = {}
agent_tokens = {}

@app.post("/v2/agent_tokens")
async def create_agent_token(request: Request):
    """Create agent token"""
    import secrets
    data = await request.json()
    token = secrets.token_urlsafe(32)
    agent_tokens[token] = data
    return {"token": token, "agent_name": data.get("name")}

@app.get("/v2/agents")
async def list_agents():
    """List registered agents"""
    return list(agents_store.values())

@app.post("/v2/agents/register")
async def register_agent(request: Request):
    """Register an agent"""
    data = await request.json()
    agent_id = data.get("agent_id", f"agent_{len(agents_store)}")
    agents_store[agent_id] = {
        "id": agent_id,
        "name": data.get("name"),
        "type": data.get("type"),
        "status": "online",
        "capabilities": data.get("capabilities", [])
    }
    return {"agent_id": agent_id, "status": "registered"}

@app.post("/v2/agents/heartbeat")
async def agent_heartbeat(request: Request):
    """Agent heartbeat"""
    data = await request.json()
    agent_id = data.get("agent_id")
    if agent_id in agents_store:
        agents_store[agent_id]["last_heartbeat"] = "now"
        return {"status": "ok"}
    return {"status": "unknown"}

@app.post("/v2/agents/lease")
async def lease_job(request: Request):
    """Lease a job for an agent"""
    # In a real implementation, this would return pending jobs
    return None

@app.get("/v2/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status"""
    return {
        "id": job_id,
        "status": "completed",
        "result": {}
    }

@app.post("/v2/jobs/{job_id}/complete")
async def complete_job(job_id: str, request: Request):
    """Mark job as complete"""
    return {"status": "acknowledged"}

# V2 Engagement endpoints (basic implementation)
engagements = {}

@app.post("/v2/engagements")
async def create_engagement(request: Request):
    """Create an engagement"""
    data = await request.json()
    engagement_id = f"eng_{len(engagements)}"
    engagements[engagement_id] = data
    return {"id": engagement_id, "status": "created"}

@app.get("/v2/engagements/{engagement_id}")
async def get_engagement(engagement_id: str):
    """Get engagement details"""
    if engagement_id in engagements:
        return engagements[engagement_id]
    return {"error": "Not found"}

# V2 Run endpoints (basic implementation)
runs = {}

@app.post("/v2/runs")
async def create_run(request: Request):
    """Create a test run"""
    data = await request.json()
    run_id = f"run_{len(runs)}"
    runs[run_id] = {
        "id": run_id,
        "engagement_id": data.get("engagement_id"),
        "status": "running"
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