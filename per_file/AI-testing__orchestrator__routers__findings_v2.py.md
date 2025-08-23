# File: AI-testing/orchestrator/routers/findings_v2.py

- Size: 20343 bytes
- Kind: text
- SHA256: 07348a92aa84dad09d1f7afeb1642b287c09738b4e70e439801c4df0244fdb61

## Python Imports

```
auth, database, datetime, fastapi, hashlib, json, models, pydantic, sqlalchemy, typing
```

## Head (first 60 lines)

```
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
```

## Tail (last 60 lines)

```
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
```

