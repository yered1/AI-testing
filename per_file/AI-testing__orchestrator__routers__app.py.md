# File: AI-testing/orchestrator/routers/app.py

- Size: 39402 bytes
- Kind: text
- SHA256: f71f4c4ca495a880cfe7893051d63fd3c68daf4adb507fcec5633180f4f6a0c6

## Python Imports

```
agents, auth, bcrypt, catalog, contextlib, datetime, engagements, fastapi, findings, hashlib, jobs, jwt, logging, models, os, plans, pydantic, reports, routers, runs, services, typing
```

## Head (first 60 lines)

```
# orchestrator/app.py
"""Main FastAPI application"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os

from routers import (
    auth_router,
    engagements_router,
    plans_router,
    runs_router,
    jobs_router,
    agents_router,
    findings_router,
    reports_router,
    catalog_router
)
from models import init_db
from services.scheduler import Scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = Scheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting AI-Testing Orchestrator...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Start scheduler
    await scheduler.start()
    logger.info("Job scheduler started")
    
    yield
    
    # Cleanup
    await scheduler.stop()
    logger.info("Shutting down AI-Testing Orchestrator...")

# Create FastAPI app
app = FastAPI(
    title="AI-Testing Platform",
    description="Distributed Security Testing Orchestration Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

```

## Tail (last 60 lines)

```
@router.get("/")
async def get_catalog(
    token_data: dict = Depends(verify_token)
):
    """Get test catalog"""
    return TEST_CATALOG

@router.get("/tests")
async def get_tests(
    category: str = None,
    agent_type: str = None,
    token_data: dict = Depends(verify_token)
):
    """Get available tests"""
    tests = TEST_CATALOG["tests"]
    
    if category:
        tests = [t for t in tests if t["category"] == category]
    
    if agent_type:
        tests = [t for t in tests if t["agent_type"] == agent_type]
    
    return tests

@router.get("/packs")
async def get_packs(
    token_data: dict = Depends(verify_token)
):
    """Get test packs"""
    return TEST_CATALOG["packs"]

@router.get("/tests/{test_id}")
async def get_test(
    test_id: str,
    token_data: dict = Depends(verify_token)
):
    """Get test details"""
    for test in TEST_CATALOG["tests"]:
        if test["id"] == test_id:
            return test
    
    raise HTTPException(status_code=404, detail="Test not found")

@router.get("/packs/{pack_id}")
async def get_pack(
    pack_id: str,
    token_data: dict = Depends(verify_token)
):
    """Get pack details"""
    for pack in TEST_CATALOG["packs"]:
        if pack["id"] == pack_id:
            # Expand tests
            pack_details = pack.copy()
            pack_details["test_details"] = [
                test for test in TEST_CATALOG["tests"]
                if test["id"] in pack["tests"]
            ]
            return pack_details
    
    raise HTTPException(status_code=404, detail="Pack not found")
```

