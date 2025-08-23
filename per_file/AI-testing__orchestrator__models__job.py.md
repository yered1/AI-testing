# File: AI-testing/orchestrator/models/job.py

- Size: 1511 bytes
- Kind: text
- SHA256: 77fa2114902d5422055881984a05ef4aacb8aa856c3a8274d73672471368403f

## Python Imports

```
base, enum, sqlalchemy, uuid
```

## Head (first 60 lines)

```
# ============================================
# orchestrator/models/job.py
"""Job queue model for agent tasks"""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text, Enum, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid
import enum

class JobStatus(enum.Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"))
    test_id = Column(String, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED)
    priority = Column(Integer, default=0)
    parameters = Column(JSON, default=dict)
    result = Column(JSON)
    error_message = Column(Text)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    assigned_at = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    run = relationship("Run", back_populates="jobs")
    agent = relationship("Agent", back_populates="jobs")
    findings = relationship("Finding", back_populates="job")
```

