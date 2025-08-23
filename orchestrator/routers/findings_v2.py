# orchestrator/routers/findings_v2.py
"""
Enhanced findings management router with structured vulnerability tracking
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import json
import hashlib

from ..database import get_db
from ..models import Finding, Run, Engagement, Agent
from ..auth import get_current_tenant

router = APIRouter(prefix="/v2/findings", tags=["findings_v2"])

class FindingCreate(BaseModel):
    """Model for creating a new finding"""
    run_id: str
    job_id: Optional[str] = None
    agent_id: Optional[str] = None
    title: str
    severity: str = Field(..., pattern="^(critical|high|medium|low|info)$")
    category: str
    description: str
    evidence: Optional[Dict[str, Any]] = None
    affected_hosts: Optional[List[str]] = []
    affected_urls: Optional[List[str]] = []
    cve_ids: Optional[List[str]] = []
    cwe_ids: Optional[List[str]] = []
    owasp_category: Optional[str] = None
    cvss_vector: Optional[str] = None
    cvss_score: Optional[float] = None
    remediation: Optional[str] = None
    references: Optional[List[str]] = []
    false_positive: bool = False
    duplicate_of: Optional[str] = None
    
class FindingUpdate(BaseModel):
    """Model for updating a finding"""
    severity: Optional[str] = Field(None, pattern="^(critical|high|medium|low|info)$")
    false_positive: Optional[bool] = None
    duplicate_of: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(open|in_progress|resolved|accepted|false_positive)$")
    notes: Optional[str] = None
    
class FindingResponse(BaseModel):
    """Response model for findings"""
    id: str
    run_id: str
    engagement_id: str
    title: str
    severity: str
    category: str
    description: str
    evidence: Optional[Dict[str, Any]]
    affected_hosts: List[str]
    affected_urls: List[str]
    cve_ids: List[str]
    cwe_ids: List[str]
    owasp_category: Optional[str]
    cvss_score: Optional[float]
    status: str
    created_at: datetime
    updated_at: datetime
    agent_name: Optional[str]
    false_positive: bool
    duplicate_of: Optional[str]
    hash: str

@router.post("/", response_model=FindingResponse)
async def create_finding(
    finding: FindingCreate,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Create a new finding from agent or manual input"""
    
    # Verify run exists and belongs to tenant
    run = await db.get(Run, finding.run_id)
    if not run or run.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Generate finding hash for deduplication
    hash_input = f"{finding.title}:{finding.category}:{finding.severity}"
    if finding.affected_hosts:
        hash_input += f":{','.join(sorted(finding.affected_hosts))}"
    if finding.affected_urls:
        hash_input += f":{','.join(sorted(finding.affected_urls))}"
    finding_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    # Check for duplicates within the same engagement
    existing = await db.execute(
        select(Finding).where(
            and_(
                Finding.engagement_id == run.engagement_id,
                Finding.hash == finding_hash,
                Finding.false_positive == False
            )
        )
    )
    duplicate = existing.scalar_one_or_none()
    
    # Create finding record
    db_finding = Finding(
        id=f"f_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{finding_hash[:8]}",
        tenant_id=tenant_id,
        run_id=finding.run_id,
        engagement_id=run.engagement_id,
        job_id=finding.job_id,
        agent_id=finding.agent_id,
        title=finding.title,
        severity=finding.severity,
        category=finding.category,
        description=finding.description,
        evidence=finding.evidence or {},
        affected_hosts=finding.affected_hosts or [],
        affected_urls=finding.affected_urls or [],
        cve_ids=finding.cve_ids or [],
        cwe_ids=finding.cwe_ids or [],
        owasp_category=finding.owasp_category,
        cvss_vector=finding.cvss_vector,
        cvss_score=finding.cvss_score,
        remediation=finding.remediation,
        references=finding.references or [],
        false_positive=finding.false_positive,
        duplicate_of=duplicate.id if duplicate else finding.duplicate_of,
        status="duplicate" if duplicate else "open",
        hash=finding_hash,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_finding)
    await db.commit()
    await db.refresh(db_finding)
    
    # Get agent name if available
    agent_name = None
    if finding.agent_id:
        agent = await db.get(Agent, finding.agent_id)
        if agent:
            agent_name = agent.name
    
    return FindingResponse(
        id=db_finding.id,
        run_id=db_finding.run_id,
        engagement_id=db_finding.engagement_id,
        title=db_finding.title,
        severity=db_finding.severity,
        category=db_finding.category,
        description=db_finding.description,
        evidence=db_finding.evidence,
        affected_hosts=db_finding.affected_hosts,
        affected_urls=db_finding.affected_urls,
        cve_ids=db_finding.cve_ids,
        cwe_ids=db_finding.cwe_ids,
        owasp_category=db_finding.owasp_category,
        cvss_score=db_finding.cvss_score,
        status=db_finding.status,
        created_at=db_finding.created_at,
        updated_at=db_finding.updated_at,
        agent_name=agent_name,
        false_positive=db_finding.false_positive,
        duplicate_of=db_finding.duplicate_of,
        hash=db_finding.hash
    )

@router.get("/run/{run_id}", response_model=List[FindingResponse])
async def get_run_findings(
    run_id: str,
    severity: Optional[str] = Query(None, pattern="^(critical|high|medium|low|info)$"),
    category: Optional[str] = None,
    exclude_false_positives: bool = True,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Get all findings for a specific run"""
    
    # Verify run exists and belongs to tenant
    run = await db.get(Run, run_id)
    if not run or run.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Build query
    query = select(Finding).where(
        and_(
            Finding.run_id == run_id,
            Finding.tenant_id == tenant_id
        )
    )
    
    if severity:
        query = query.where(Finding.severity == severity)
    if category:
        query = query.where(Finding.category == category)
    if exclude_false_positives:
        query = query.where(Finding.false_positive == False)
    
    query = query.order_by(
        desc(Finding.severity == "critical"),
        desc(Finding.severity == "high"),
        desc(Finding.severity == "medium"),
        desc(Finding.severity == "low"),
        desc(Finding.created_at)
    )
    
    result = await db.execute(query)
    findings = result.scalars().all()
    
    # Get agent names
    agent_names = {}
    for f in findings:
        if f.agent_id and f.agent_id not in agent_names:
            agent = await db.get(Agent, f.agent_id)
            if agent:
                agent_names[f.agent_id] = agent.name
    
    return [
        FindingResponse(
            id=f.id,
            run_id=f.run_id,
            engagement_id=f.engagement_id,
            title=f.title,
            severity=f.severity,
            category=f.category,
            description=f.description,
            evidence=f.evidence,
            affected_hosts=f.affected_hosts,
            affected_urls=f.affected_urls,
            cve_ids=f.cve_ids,
            cwe_ids=f.cwe_ids,
            owasp_category=f.owasp_category,
            cvss_score=f.cvss_score,
            status=f.status,
            created_at=f.created_at,
            updated_at=f.updated_at,
            agent_name=agent_names.get(f.agent_id),
            false_positive=f.false_positive,
            duplicate_of=f.duplicate_of,
            hash=f.hash
        )
        for f in findings
    ]

@router.get("/engagement/{engagement_id}", response_model=List[FindingResponse])
async def get_engagement_findings(
    engagement_id: str,
    severity: Optional[str] = Query(None, pattern="^(critical|high|medium|low|info)$"),
    unique_only: bool = True,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Get all findings for an engagement (across all runs)"""
    
    # Verify engagement exists and belongs to tenant
    engagement = await db.get(Engagement, engagement_id)
    if not engagement or engagement.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Build query
    query = select(Finding).where(
        and_(
            Finding.engagement_id == engagement_id,
            Finding.tenant_id == tenant_id,
            Finding.false_positive == False
        )
    )
    
    if severity:
        query = query.where(Finding.severity == severity)
    
    if unique_only:
        # Only get non-duplicate findings
        query = query.where(Finding.duplicate_of == None)
    
    query = query.order_by(
        desc(Finding.severity == "critical"),
        desc(Finding.severity == "high"),
        desc(Finding.severity == "medium"),
        desc(Finding.severity == "low"),
        desc(Finding.created_at)
    )
    
    result = await db.execute(query)
    findings = result.scalars().all()
    
    # Get agent names
    agent_names = {}
    for f in findings:
        if f.agent_id and f.agent_id not in agent_names:
            agent = await db.get(Agent, f.agent_id)
            if agent:
                agent_names[f.agent_id] = agent.name
    
    return [
        FindingResponse(
            id=f.id,
            run_id=f.run_id,
            engagement_id=f.engagement_id,
            title=f.title,
            severity=f.severity,
            category=f.category,
            description=f.description,
            evidence=f.evidence,
            affected_hosts=f.affected_hosts,
            affected_urls=f.affected_urls,
            cve_ids=f.cve_ids,
            cwe_ids=f.cwe_ids,
            owasp_category=f.owasp_category,
            cvss_score=f.cvss_score,
            status=f.status,
            created_at=f.created_at,
            updated_at=f.updated_at,
            agent_name=agent_names.get(f.agent_id),
            false_positive=f.false_positive,
            duplicate_of=f.duplicate_of,
            hash=f.hash
        )
        for f in findings
    ]

@router.get("/stats/{engagement_id}")
async def get_finding_stats(
    engagement_id: str,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics about findings for an engagement"""
    
    # Verify engagement exists and belongs to tenant
    engagement = await db.get(Engagement, engagement_id)
    if not engagement or engagement.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    # Get severity counts
    severity_counts = await db.execute(
        select(
            Finding.severity,
            func.count(Finding.id).label("count")
        ).where(
            and_(
                Finding.engagement_id == engagement_id,
                Finding.tenant_id == tenant_id,
                Finding.false_positive == False,
                Finding.duplicate_of == None
            )
        ).group_by(Finding.severity)
    )
    
    # Get category counts
    category_counts = await db.execute(
        select(
            Finding.category,
            func.count(Finding.id).label("count")
        ).where(
            and_(
                Finding.engagement_id == engagement_id,
                Finding.tenant_id == tenant_id,
                Finding.false_positive == False,
                Finding.duplicate_of == None
            )
        ).group_by(Finding.category)
    )
    
    # Get OWASP category counts
    owasp_counts = await db.execute(
        select(
            Finding.owasp_category,
            func.count(Finding.id).label("count")
        ).where(
            and_(
                Finding.engagement_id == engagement_id,
                Finding.tenant_id == tenant_id,
                Finding.false_positive == False,
                Finding.duplicate_of == None,
                Finding.owasp_category != None
            )
        ).group_by(Finding.owasp_category)
    )
    
    severity_stats = {row.severity: row.count for row in severity_counts}
    category_stats = {row.category: row.count for row in category_counts}
    owasp_stats = {row.owasp_category: row.count for row in owasp_counts}
    
    # Get total counts
    total_query = await db.execute(
        select(func.count(Finding.id)).where(
            and_(
                Finding.engagement_id == engagement_id,
                Finding.tenant_id == tenant_id
            )
        )
    )
    total_findings = total_query.scalar()
    
    unique_query = await db.execute(
        select(func.count(Finding.id)).where(
            and_(
                Finding.engagement_id == engagement_id,
                Finding.tenant_id == tenant_id,
                Finding.duplicate_of == None,
                Finding.false_positive == False
            )
        )
    )
    unique_findings = unique_query.scalar()
    
    return {
        "engagement_id": engagement_id,
        "total_findings": total_findings,
        "unique_findings": unique_findings,
        "severity_distribution": severity_stats,
        "category_distribution": category_stats,
        "owasp_distribution": owasp_stats,
        "critical_count": severity_stats.get("critical", 0),
        "high_count": severity_stats.get("high", 0),
        "medium_count": severity_stats.get("medium", 0),
        "low_count": severity_stats.get("low", 0),
        "info_count": severity_stats.get("info", 0)
    }

@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: str,
    update: FindingUpdate,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Update a finding (mark as false positive, change status, etc.)"""
    
    finding = await db.get(Finding, finding_id)
    if not finding or finding.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # Update fields
    if update.severity is not None:
        finding.severity = update.severity
    if update.false_positive is not None:
        finding.false_positive = update.false_positive
    if update.duplicate_of is not None:
        finding.duplicate_of = update.duplicate_of
    if update.status is not None:
        finding.status = update.status
    if update.notes is not None:
        if not finding.evidence:
            finding.evidence = {}
        finding.evidence["notes"] = update.notes
    
    finding.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(finding)
    
    # Get agent name if available
    agent_name = None
    if finding.agent_id:
        agent = await db.get(Agent, finding.agent_id)
        if agent:
            agent_name = agent.name
    
    return FindingResponse(
        id=finding.id,
        run_id=finding.run_id,
        engagement_id=finding.engagement_id,
        title=finding.title,
        severity=finding.severity,
        category=finding.category,
        description=finding.description,
        evidence=finding.evidence,
        affected_hosts=finding.affected_hosts,
        affected_urls=finding.affected_urls,
        cve_ids=finding.cve_ids,
        cwe_ids=finding.cwe_ids,
        owasp_category=finding.owasp_category,
        cvss_score=finding.cvss_score,
        status=finding.status,
        created_at=finding.created_at,
        updated_at=finding.updated_at,
        agent_name=agent_name,
        false_positive=finding.false_positive,
        duplicate_of=finding.duplicate_of,
        hash=finding.hash
    )

@router.post("/bulk", response_model=List[FindingResponse])
async def create_bulk_findings(
    findings: List[FindingCreate],
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Create multiple findings at once (for agent batch reporting)"""
    
    if len(findings) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 findings per batch")
    
    created_findings = []
    for finding in findings:
        # Verify run exists and belongs to tenant
        run = await db.get(Run, finding.run_id)
        if not run or run.tenant_id != tenant_id:
            continue  # Skip invalid runs
        
        # Generate finding hash for deduplication
        hash_input = f"{finding.title}:{finding.category}:{finding.severity}"
        if finding.affected_hosts:
            hash_input += f":{','.join(sorted(finding.affected_hosts))}"
        if finding.affected_urls:
            hash_input += f":{','.join(sorted(finding.affected_urls))}"
        finding_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        # Check for duplicates
        existing = await db.execute(
            select(Finding).where(
                and_(
                    Finding.engagement_id == run.engagement_id,
                    Finding.hash == finding_hash,
                    Finding.false_positive == False
                )
            )
        )
        duplicate = existing.scalar_one_or_none()
        
        # Create finding record
        db_finding = Finding(
            id=f"f_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{finding_hash[:8]}",
            tenant_id=tenant_id,
            run_id=finding.run_id,
            engagement_id=run.engagement_id,
            job_id=finding.job_id,
            agent_id=finding.agent_id,
            title=finding.title,
            severity=finding.severity,
            category=finding.category,
            description=finding.description,
            evidence=finding.evidence or {},
            affected_hosts=finding.affected_hosts or [],
            affected_urls=finding.affected_urls or [],
            cve_ids=finding.cve_ids or [],
            cwe_ids=finding.cwe_ids or [],
            owasp_category=finding.owasp_category,
            cvss_vector=finding.cvss_vector,
            cvss_score=finding.cvss_score,
            remediation=finding.remediation,
            references=finding.references or [],
            false_positive=finding.false_positive,
            duplicate_of=duplicate.id if duplicate else finding.duplicate_of,
            status="duplicate" if duplicate else "open",
            hash=finding_hash,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_finding)
        created_findings.append(db_finding)
    
    await db.commit()
    
    # Get agent names
    agent_names = {}
    for f in created_findings:
        if f.agent_id and f.agent_id not in agent_names:
            agent = await db.get(Agent, f.agent_id)
            if agent:
                agent_names[f.agent_id] = agent.name
    
    return [
        FindingResponse(
            id=f.id,
            run_id=f.run_id,
            engagement_id=f.engagement_id,
            title=f.title,
            severity=f.severity,
            category=f.category,
            description=f.description,
            evidence=f.evidence,
            affected_hosts=f.affected_hosts,
            affected_urls=f.affected_urls,
            cve_ids=f.cve_ids,
            cwe_ids=f.cwe_ids,
            owasp_category=f.owasp_category,
            cvss_score=f.cvss_score,
            status=f.status,
            created_at=f.created_at,
            updated_at=f.updated_at,
            agent_name=agent_names.get(f.agent_id),
            false_positive=f.false_positive,
            duplicate_of=f.duplicate_of,
            hash=f.hash
        )
        for f in created_findings
    ]