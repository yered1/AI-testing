# File: AI-testing/orchestrator/models/plan.py

- Size: 1873 bytes
- Kind: text
- SHA256: 51463be085d6a0867cd7a9b7e6b64163c18e1a93cc4fa9592cb93c72e55a9a2e

## Python Imports

```
base, sqlalchemy, uuid
```

## Head (first 60 lines)

```
# ============================================
# orchestrator/models/plan.py
"""Test plan models"""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text, Boolean, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    engagement_id = Column(String, ForeignKey("engagements.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    engagement = relationship("Engagement", back_populates="plans")
    tests = relationship("PlanTest", back_populates="plan", cascade="all, delete-orphan")
    runs = relationship("Run", back_populates="plan", cascade="all, delete-orphan")
    approver = relationship("User", foreign_keys=[approved_by])
    creator = relationship("User", foreign_keys=[created_by])

class PlanTest(Base):
    __tablename__ = "plan_tests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String, ForeignKey("plans.id"), nullable=False)
    test_id = Column(String, nullable=False)  # Reference to test catalog
    name = Column(String, nullable=False)
    parameters = Column(JSON, default=dict)
    priority = Column(Integer, default=0)
    estimated_duration = Column(Integer)  # seconds
    
    # Relationships
    plan = relationship("Plan", back_populates="tests")
```

