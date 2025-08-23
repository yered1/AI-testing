# ============================================
# orchestrator/models/run.py
"""Test run execution model"""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text, Enum, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid
import enum

class RunStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Run(Base):
    __tablename__ = "runs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String, ForeignKey("plans.id"), nullable=False)
    status = Column(Enum(RunStatus), default=RunStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    started_by = Column(String, ForeignKey("users.id"))
    error_message = Column(Text)
    statistics = Column(JSON, default=dict)  # {"total_jobs": 0, "completed": 0, "failed": 0}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    plan = relationship("Plan", back_populates="runs")
    jobs = relationship("Job", back_populates="run", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="run", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")
    starter = relationship("User")