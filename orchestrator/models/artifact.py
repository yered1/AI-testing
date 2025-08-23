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
