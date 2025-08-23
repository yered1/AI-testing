# File: AI-testing/orchestrator/models/artifact.py

- Size: 912 bytes
- Kind: text
- SHA256: f0b04b93af79ef82f370ce9ef27ab260475bc098c1ce856571347137eef129a6

## Python Imports

```
base, sqlalchemy, uuid
```

## Head (first 60 lines)

```
# ============================================
# orchestrator/models/artifact.py
"""Artifact storage model"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid

class Artifact(Base):
    __tablename__ = "artifacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id"))
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)  # Storage path
    mime_type = Column(String)
    size = Column(Integer)  # bytes
    checksum = Column(String)  # SHA256
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    run = relationship("Run", back_populates="artifacts")
```

