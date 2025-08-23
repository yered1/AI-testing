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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Mount routers
app.include_router(auth_router, prefix="/api/v2/auth", tags=["Authentication"])
app.include_router(engagements_router, prefix="/api/v2/engagements", tags=["Engagements"])
app.include_router(plans_router, prefix="/api/v2/plans", tags=["Plans"])
app.include_router(runs_router, prefix="/api/v2/runs", tags=["Runs"])
app.include_router(jobs_router, prefix="/api/v2/jobs", tags=["Jobs"])
app.include_router(agents_router, prefix="/api/v2/agents", tags=["Agents"])
app.include_router(findings_router, prefix="/api/v2/findings", tags=["Findings"])
app.include_router(reports_router, prefix="/api/v2/reports", tags=["Reports"])
app.include_router(catalog_router, prefix="/api/v2/catalog", tags=["Catalog"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AI-Testing Platform",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "version": "2.0.0"
    }

# ============================================
# orchestrator/routers/__init__.py
"""API routers"""

from .auth import router as auth_router
from .engagements import router as engagements_router
from .plans import router as plans_router
from .runs import router as runs_router
from .jobs import router as jobs_router
from .agents import router as agents_router
from .findings import router as findings_router
from .reports import router as reports_router
from .catalog import router as catalog_router

__all__ = [
    'auth_router',
    'engagements_router',
    'plans_router',
    'runs_router',
    'jobs_router',
    'agents_router',
    'findings_router',
    'reports_router',
    'catalog_router'
]

# ============================================
# orchestrator/routers/auth.py
"""Authentication endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
import os

from models import get_db, User, Tenant

router = APIRouter()
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    tenant_name: Optional[str] = "default"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register new user"""
    with get_db() as db:
        # Check if user exists
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Get or create tenant
        tenant = db.query(Tenant).filter(Tenant.name == request.tenant_name).first()
        if not tenant:
            tenant = Tenant(name=request.tenant_name, display_name=request.tenant_name)
            db.add(tenant)
            db.flush()
        
        # Hash password
        password_hash = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt()).decode()
        
        # Create user
        user = User(
            tenant_id=tenant.id,
            email=request.email,
            username=request.username,
            password_hash=password_hash,
            role="user"
        )
        db.add(user)
        db.commit()
        
        # Create token
        access_token = create_access_token({
            "sub": user.id,
            "email": user.email,
            "tenant_id": tenant.id,
            "role": user.role
        })
        
        return TokenResponse(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login user"""
    with get_db() as db:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not bcrypt.checkpw(request.password.encode(), user.password_hash.encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create token
        access_token = create_access_token({
            "sub": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id,
            "role": user.role
        })
        
        return TokenResponse(
            access_token=access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

# ============================================
# orchestrator/routers/engagements.py
"""Engagement management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from models import get_db, Engagement, EngagementType, EngagementStatus
from .auth import verify_token

router = APIRouter()

class ScopeModel(BaseModel):
    targets: List[str]
    exclude: List[str] = []

class EngagementCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: str
    scope: ScopeModel

class EngagementResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    type: str
    status: str
    scope: dict
    created_at: datetime

@router.post("/", response_model=EngagementResponse)
async def create_engagement(
    engagement: EngagementCreate,
    token_data: dict = Depends(verify_token)
):
    """Create new engagement"""
    with get_db() as db:
        # Map string to enum
        try:
            eng_type = EngagementType[engagement.type.upper().replace("-", "_")]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid engagement type: {engagement.type}")
        
        new_engagement = Engagement(
            tenant_id=token_data["tenant_id"],
            name=engagement.name,
            description=engagement.description,
            type=eng_type,
            scope=engagement.scope.dict(),
            created_by=token_data["sub"],
            status=EngagementStatus.ACTIVE
        )
        
        db.add(new_engagement)
        db.commit()
        db.refresh(new_engagement)
        
        return EngagementResponse(
            id=new_engagement.id,
            tenant_id=new_engagement.tenant_id,
            name=new_engagement.name,
            description=new_engagement.description,
            type=new_engagement.type.value,
            status=new_engagement.status.value,
            scope=new_engagement.scope,
            created_at=new_engagement.created_at
        )

@router.get("/", response_model=List[EngagementResponse])
async def list_engagements(
    status: Optional[str] = Query(None),
    token_data: dict = Depends(verify_token)
):
    """List engagements for tenant"""
    with get_db() as db:
        query = db.query(Engagement).filter(
            Engagement.tenant_id == token_data["tenant_id"]
        )
        
        if status:
            query = query.filter(Engagement.status == status)
        
        engagements = query.all()
        
        return [
            EngagementResponse(
                id=e.id,
                tenant_id=e.tenant_id,
                name=e.name,
                description=e.description,
                type=e.type.value,
                status=e.status.value,
                scope=e.scope,
                created_at=e.created_at
            )
            for e in engagements
        ]

@router.get("/{engagement_id}", response_model=EngagementResponse)
async def get_engagement(
    engagement_id: str,
    token_data: dict = Depends(verify_token)
):
    """Get engagement details"""
    with get_db() as db:
        engagement = db.query(Engagement).filter(
            Engagement.id == engagement_id,
            Engagement.tenant_id == token_data["tenant_id"]
        ).first()
        
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        
        return EngagementResponse(
            id=engagement.id,
            tenant_id=engagement.tenant_id,
            name=engagement.name,
            description=engagement.description,
            type=engagement.type.value,
            status=engagement.status.value,
            scope=engagement.scope,
            created_at=engagement.created_at
        )

# ============================================
# orchestrator/routers/plans.py
"""Test plan endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from models import get_db, Plan, PlanTest, Engagement
from .auth import verify_token

router = APIRouter()

class TestConfig(BaseModel):
    test_id: str
    parameters: Optional[Dict] = {}

class PlanCreate(BaseModel):
    engagement_id: str
    name: str
    description: Optional[str] = None
    tests: List[TestConfig]

class PlanResponse(BaseModel):
    id: str
    engagement_id: str
    name: str
    description: Optional[str]
    is_approved: bool
    tests: List[dict]
    created_at: datetime

@router.post("/", response_model=PlanResponse)
async def create_plan(
    plan: PlanCreate,
    token_data: dict = Depends(verify_token)
):
    """Create test plan"""
    with get_db() as db:
        # Verify engagement exists and belongs to tenant
        engagement = db.query(Engagement).filter(
            Engagement.id == plan.engagement_id,
            Engagement.tenant_id == token_data["tenant_id"]
        ).first()
        
        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")
        
        # Create plan
        new_plan = Plan(
            engagement_id=plan.engagement_id,
            name=plan.name,
            description=plan.description,
            created_by=token_data["sub"]
        )
        
        db.add(new_plan)
        db.flush()
        
        # Add tests
        for idx, test in enumerate(plan.tests):
            plan_test = PlanTest(
                plan_id=new_plan.id,
                test_id=test.test_id,
                name=test.test_id,  # Will be resolved from catalog
                parameters=test.parameters,
                priority=idx
            )
            db.add(plan_test)
        
        db.commit()
        db.refresh(new_plan)
        
        return PlanResponse(
            id=new_plan.id,
            engagement_id=new_plan.engagement_id,
            name=new_plan.name,
            description=new_plan.description,
            is_approved=new_plan.is_approved,
            tests=[
                {
                    "test_id": t.test_id,
                    "parameters": t.parameters
                }
                for t in new_plan.tests
            ],
            created_at=new_plan.created_at
        )

@router.post("/{plan_id}/approve")
async def approve_plan(
    plan_id: str,
    token_data: dict = Depends(verify_token)
):
    """Approve plan for execution"""
    with get_db() as db:
        plan = db.query(Plan).join(Engagement).filter(
            Plan.id == plan_id,
            Engagement.tenant_id == token_data["tenant_id"]
        ).first()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        plan.is_approved = True
        plan.approved_by = token_data["sub"]
        plan.approved_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Plan approved"}

# ============================================
# orchestrator/routers/runs.py
"""Test run execution endpoints"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from models import get_db, Run, RunStatus, Plan, Job, JobStatus, Engagement
from services.scheduler import scheduler
from .auth import verify_token

router = APIRouter()

class RunCreate(BaseModel):
    plan_id: str

class RunResponse(BaseModel):
    id: str
    plan_id: str
    status: str
    progress: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

@router.post("/", response_model=RunResponse)
async def create_run(
    run_request: RunCreate,
    background_tasks: BackgroundTasks,
    token_data: dict = Depends(verify_token)
):
    """Start test run"""
    with get_db() as db:
        # Verify plan exists and is approved
        plan = db.query(Plan).join(Engagement).filter(
            Plan.id == run_request.plan_id,
            Engagement.tenant_id == token_data["tenant_id"]
        ).first()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        if not plan.is_approved:
            raise HTTPException(status_code=400, detail="Plan not approved")
        
        # Create run
        new_run = Run(
            plan_id=run_request.plan_id,
            status=RunStatus.PENDING,
            started_by=token_data["sub"],
            started_at=datetime.utcnow()
        )
        
        db.add(new_run)
        db.flush()
        
        # Create jobs for each test
        for test in plan.tests:
            job = Job(
                run_id=new_run.id,
                test_id=test.test_id,
                parameters=test.parameters,
                priority=test.priority,
                status=JobStatus.QUEUED
            )
            db.add(job)
        
        db.commit()
        db.refresh(new_run)
        
        # Schedule run execution
        background_tasks.add_task(scheduler.execute_run, new_run.id)
        
        return RunResponse(
            id=new_run.id,
            plan_id=new_run.plan_id,
            status=new_run.status.value,
            progress=new_run.progress,
            started_at=new_run.started_at,
            completed_at=new_run.completed_at
        )

@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    token_data: dict = Depends(verify_token)
):
    """Get run status"""
    with get_db() as db:
        run = db.query(Run).join(Plan).join(Engagement).filter(
            Run.id == run_id,
            Engagement.tenant_id == token_data["tenant_id"]
        ).first()
        
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        return RunResponse(
            id=run.id,
            plan_id=run.plan_id,
            status=run.status.value,
            progress=run.progress,
            started_at=run.started_at,
            completed_at=run.completed_at
        )

@router.post("/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    token_data: dict = Depends(verify_token)
):
    """Cancel running test"""
    with get_db() as db:
        run = db.query(Run).join(Plan).join(Engagement).filter(
            Run.id == run_id,
            Engagement.tenant_id == token_data["tenant_id"]
        ).first()
        
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        if run.status not in [RunStatus.PENDING, RunStatus.RUNNING]:
            raise HTTPException(status_code=400, detail="Run cannot be cancelled")
        
        run.status = RunStatus.CANCELLED
        run.completed_at = datetime.utcnow()
        
        # Cancel all pending jobs
        db.query(Job).filter(
            Job.run_id == run_id,
            Job.status.in_([JobStatus.QUEUED, JobStatus.ASSIGNED])
        ).update({Job.status: JobStatus.CANCELLED})
        
        db.commit()
        
        return {"message": "Run cancelled"}

# ============================================
# orchestrator/routers/agents.py
"""Agent management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import hashlib

from models import get_db, Agent, AgentToken, AgentType, AgentStatus, Job, JobStatus
from .auth import verify_token

router = APIRouter()

class AgentRegister(BaseModel):
    name: str
    type: str
    version: Optional[str] = "1.0.0"
    capabilities: List[str] = []

class AgentTokenCreate(BaseModel):
    agent_name: str
    agent_type: str

class TokenResponse(BaseModel):
    token: str
    agent_id: str

class JobLease(BaseModel):
    agent_type: str

class JobResponse(BaseModel):
    id: str
    test_id: str
    parameters: dict
    run_id: str

@router.post("/register", response_model=dict)
async def register_agent(
    agent_data: AgentRegister,
    authorization: str = Header(None)
):
    """Register new agent"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = authorization.replace("Bearer ", "")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    with get_db() as db:
        # Verify token
        agent_token = db.query(AgentToken).filter(
            AgentToken.token_hash == token_hash,
            AgentToken.is_active == True
        ).first()
        
        if not agent_token:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Update agent
        agent = agent_token.agent
        agent.status = AgentStatus.ONLINE
        agent.last_heartbeat = datetime.utcnow()
        agent.version = agent_data.version
        agent.capabilities = agent_data.capabilities
        
        db.commit()
        
        return {"agent_id": agent.id, "status": "registered"}

@router.post("/token", response_model=TokenResponse)
async def create_agent_token(
    request: AgentTokenCreate,
    token_data: dict = Depends(verify_token)
):
    """Create agent authentication token"""
    with get_db() as db:
        # Map type
        try:
            agent_type = AgentType[request.agent_type.upper()]
        except KeyError:
            agent_type = AgentType.CUSTOM
        
        # Create agent
        agent = Agent(
            tenant_id=token_data["tenant_id"],
            name=request.agent_name,
            type=agent_type,
            status=AgentStatus.OFFLINE
        )
        db.add(agent)
        db.flush()
        
        # Generate token
        raw_token = AgentToken.generate_token()
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # Create token
        agent_token = AgentToken(
            agent_id=agent.id,
            token_hash=token_hash,
            name=f"{request.agent_name}_token"
        )
        db.add(agent_token)
        db.commit()
        
        return TokenResponse(token=raw_token, agent_id=agent.id)

@router.post("/lease", response_model=Optional[JobResponse])
async def lease_job(
    lease_request: JobLease,
    authorization: str = Header(None)
):
    """Lease job for agent"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No jobs available")
    
    token = authorization.replace("Bearer ", "")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    with get_db() as db:
        # Verify token
        agent_token = db.query(AgentToken).filter(
            AgentToken.token_hash == token_hash,
            AgentToken.is_active == True
        ).first()
        
        if not agent_token:
            raise HTTPException(status_code=401, detail="No jobs available")
        
        agent = agent_token.agent
        
        # Update heartbeat
        agent.last_heartbeat = datetime.utcnow()
        agent.status = AgentStatus.ONLINE
        
        # Find available job
        job = db.query(Job).filter(
            Job.status == JobStatus.QUEUED
        ).order_by(Job.priority.desc(), Job.created_at).first()
        
        if not job:
            db.commit()
            return None
        
        # Assign job
        job.agent_id = agent.id
        job.status = JobStatus.ASSIGNED
        job.assigned_at = datetime.utcnow()
        
        db.commit()
        
        return JobResponse(
            id=job.id,
            test_id=job.test_id,
            parameters=job.parameters,
            run_id=job.run_id
        )

@router.post("/heartbeat")
async def agent_heartbeat(
    authorization: str = Header(None)
):
    """Agent heartbeat"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    with get_db() as db:
        agent_token = db.query(AgentToken).filter(
            AgentToken.token_hash == token_hash,
            AgentToken.is_active == True
        ).first()
        
        if not agent_token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        agent = agent_token.agent
        agent.last_heartbeat = datetime.utcnow()
        agent.status = AgentStatus.ONLINE
        
        db.commit()
        
        return {"status": "ok"}

# ============================================
# orchestrator/routers/jobs.py
"""Job management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib

from models import get_db, Job, JobStatus, AgentToken
from .auth import verify_token

router = APIRouter()

class JobUpdate(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

@router.post("/{job_id}/complete")
async def complete_job(
    job_id: str,
    update: JobUpdate,
    authorization: str = Header(None)
):
    """Mark job as complete"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = authorization.replace("Bearer ", "")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    with get_db() as db:
        # Verify token
        agent_token = db.query(AgentToken).filter(
            AgentToken.token_hash == token_hash,
            AgentToken.is_active == True
        ).first()
        
        if not agent_token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # Get job
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.agent_id == agent_token.agent_id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update job
        try:
            job.status = JobStatus[update.status.upper()]
        except KeyError:
            job.status = JobStatus.FAILED
        
        job.result = update.result
        job.error_message = update.error_message
        job.completed_at = datetime.utcnow()
        
        # Update agent status
        agent_token.agent.status = AgentStatus.ONLINE
        
        db.commit()
        
        return {"message": "Job updated"}

@router.get("/{job_id}")
async def get_job(
    job_id: str,
    token_data: dict = Depends(verify_token)
):
    """Get job details"""
    with get_db() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "id": job.id,
            "run_id": job.run_id,
            "test_id": job.test_id,
            "status": job.status.value,
            "parameters": job.parameters,
            "result": job.result,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "completed_at": job.completed_at
        }

# ============================================
# orchestrator/routers/findings.py
"""Security findings endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from models import get_db, Finding, Severity, FindingStatus, Run, Plan, Engagement
from .auth import verify_token

router = APIRouter()

class FindingResponse(BaseModel):
    id: str
    run_id: str
    title: str
    description: Optional[str]
    severity: str
    status: str
    vulnerability_type: Optional[str]
    affected_component: Optional[str]
    created_at: datetime

@router.get("/run/{run_id}", response_model=List[FindingResponse])
async def get_run_findings(
    run_id: str,
    severity: Optional[str] = None,
    token_data: dict = Depends(verify_token)
):
    """Get findings for a run"""
    with get_db() as db:
        # Verify access
        run = db.query(Run).join(Plan).join(Engagement).filter(
            Run.id == run_id,
            Engagement.tenant_id == token_data["tenant_id"]
        ).first()
        
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        query = db.query(Finding).filter(Finding.run_id == run_id)
        
        if severity:
            query = query.filter(Finding.severity == severity)
        
        findings = query.all()
        
        return [
            FindingResponse(
                id=f.id,
                run_id=f.run_id,
                title=f.title,
                description=f.description,
                severity=f.severity.value,
                status=f.status.value,
                vulnerability_type=f.vulnerability_type,
                affected_component=f.affected_component,
                created_at=f.created_at
            )
            for f in findings
        ]

@router.patch("/{finding_id}/status")
async def update_finding_status(
    finding_id: str,
    status: str,
    token_data: dict = Depends(verify_token)
):
    """Update finding status"""
    with get_db() as db:
        finding = db.query(Finding).join(Run).join(Plan).join(Engagement).filter(
            Finding.id == finding_id,
            Engagement.tenant_id == token_data["tenant_id"]
        ).first()
        
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        
        try:
            finding.status = FindingStatus[status.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        db.commit()
        
        return {"message": "Status updated"}

# ============================================
# orchestrator/routers/reports.py
"""Report generation endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from typing import Optional

from models import get_db, Run, Plan, Engagement, Finding, Report, ReportFormat
from services.report_generator import ReportGenerator
from .auth import verify_token

router = APIRouter()

@router.post("/run/{run_id}/generate")
async def generate_report(
    run_id: str,
    format: str = "html",
    token_data: dict = Depends(verify_token)
):
    """Generate report for run"""
    with get_db() as db:
        # Verify access
        run = db.query(Run).join(Plan).join(Engagement).filter(
            Run.id == run_id,
            Engagement.tenant_id == token_data["tenant_id"]
        ).first()
        
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Map format
        try:
            report_format = ReportFormat[format.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid format: {format}")
        
        # Generate report
        generator = ReportGenerator()
        report_path = await generator.generate(run_id, report_format)
        
        # Save report record
        report = Report(
            run_id=run_id,
            format=report_format,
            name=f"Report_{run_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            path=report_path,
            generated_by=token_data["sub"]
        )
        db.add(report)
        db.commit()
        
        return FileResponse(
            report_path,
            media_type="application/octet-stream",
            filename=f"report_{run_id}.{format}"
        )

@router.get("/run/{run_id}")
async def get_run_report(
    run_id: str,
    token_data: dict = Depends(verify_token)
):
    """Get report data for run"""
    with get_db() as db:
        # Verify access
        run = db.query(Run).join(Plan).join(Engagement).filter(
            Run.id == run_id,
            Engagement.tenant_id == token_data["tenant_id"]
        ).first()
        
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Get findings
        findings = db.query(Finding).filter(Finding.run_id == run_id).all()
        
        # Build report data
        report_data = {
            "run_id": run.id,
            "engagement": {
                "name": run.plan.engagement.name,
                "type": run.plan.engagement.type.value,
                "scope": run.plan.engagement.scope
            },
            "plan": {
                "name": run.plan.name,
                "tests": len(run.plan.tests)
            },
            "execution": {
                "status": run.status.value,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
                "duration": (run.completed_at - run.started_at).total_seconds() if run.completed_at else None
            },
            "findings": {
                "total": len(findings),
                "critical": len([f for f in findings if f.severity == Severity.CRITICAL]),
                "high": len([f for f in findings if f.severity == Severity.HIGH]),
                "medium": len([f for f in findings if f.severity == Severity.MEDIUM]),
                "low": len([f for f in findings if f.severity == Severity.LOW]),
                "info": len([f for f in findings if f.severity == Severity.INFO])
            },
            "details": [
                {
                    "id": f.id,
                    "title": f.title,
                    "severity": f.severity.value,
                    "type": f.vulnerability_type,
                    "component": f.affected_component
                }
                for f in findings
            ]
        }
        
        return report_data

# ============================================
# orchestrator/routers/catalog.py
"""Test catalog endpoints"""

from fastapi import APIRouter, Depends
from typing import List, Dict

from .auth import verify_token

router = APIRouter()

# Static catalog for now - would be database-driven in production
TEST_CATALOG = {
    "tests": [
        {
            "id": "web_discovery",
            "name": "Web Discovery Scan",
            "description": "Discover web application structure and endpoints",
            "category": "discovery",
            "agent_type": "zap",
            "duration_estimate": 300,
            "risk_level": "safe"
        },
        {
            "id": "web_vulnerabilities",
            "name": "Web Vulnerability Scan",
            "description": "Scan for common web vulnerabilities",
            "category": "vulnerability",
            "agent_type": "zap",
            "duration_estimate": 900,
            "risk_level": "moderate"
        },
        {
            "id": "api_fuzzing",
            "name": "API Fuzzing",
            "description": "Fuzz test API endpoints",
            "category": "fuzzing",
            "agent_type": "zap",
            "duration_estimate": 600,
            "risk_level": "moderate"
        },
        {
            "id": "nuclei_scan",
            "name": "Nuclei Template Scan",
            "description": "Run Nuclei vulnerability templates",
            "category": "vulnerability",
            "agent_type": "nuclei",
            "duration_estimate": 600,
            "risk_level": "safe"
        },
        {
            "id": "code_secrets",
            "name": "Secret Detection",
            "description": "Scan code for hardcoded secrets",
            "category": "code",
            "agent_type": "semgrep",
            "duration_estimate": 300,
            "risk_level": "safe"
        },
        {
            "id": "code_sast",
            "name": "Static Application Security Testing",
            "description": "Analyze code for security issues",
            "category": "code",
            "agent_type": "semgrep",
            "duration_estimate": 900,
            "risk_level": "safe"
        },
        {
            "id": "network_discovery",
            "name": "Network Discovery",
            "description": "Discover network services and ports",
            "category": "network",
            "agent_type": "nmap",
            "duration_estimate": 600,
            "risk_level": "moderate"
        },
        {
            "id": "port_scan",
            "name": "Port Scan",
            "description": "Comprehensive port scanning",
            "category": "network",
            "agent_type": "nmap",
            "duration_estimate": 1200,
            "risk_level": "moderate"
        }
    ],
    "packs": [
        {
            "id": "quick_web",
            "name": "Quick Web Assessment",
            "description": "Fast web application security check",
            "tests": ["web_discovery", "nuclei_scan"]
        },
        {
            "id": "comprehensive_web",
            "name": "Comprehensive Web Security",
            "description": "Full web application security assessment",
            "tests": ["web_discovery", "web_vulnerabilities", "api_fuzzing", "nuclei_scan"]
        },
        {
            "id": "code_review",
            "name": "Code Security Review",
            "description": "Static code analysis for security issues",
            "tests": ["code_secrets", "code_sast"]
        },
        {
            "id": "network_assessment",
            "name": "Network Security Assessment",
            "description": "Network discovery and vulnerability assessment",
            "tests": ["network_discovery", "port_scan"]
        },
        {
            "id": "full_assessment",
            "name": "Full Security Assessment",
            "description": "Complete security testing across all vectors",
            "tests": [
                "web_discovery", "web_vulnerabilities", "api_fuzzing",
                "nuclei_scan", "code_secrets", "code_sast",
                "network_discovery", "port_scan"
            ]
        }
    ]
}

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