# ============================================
# orchestrator/models/finding.py
"""Security finding model"""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid
import enum

class Severity(enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class FindingStatus(enum.Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"

class Finding(Base):
    __tablename__ = "findings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    severity = Column(Enum(Severity), nullable=False)
    status = Column(Enum(FindingStatus), default=FindingStatus.NEW)
    vulnerability_type = Column(String)  # OWASP category, CWE, etc.
    affected_component = Column(String)  # URL, file, endpoint, etc.
    evidence = Column(JSON, default=dict)  # Screenshots, requests/responses, etc.
    remediation = Column(Text)
    cvss_score = Column(Float)
    cvss_vector = Column(String)
    references = Column(JSON, default=list)  # URLs to documentation
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    run = relationship("Run", back_populates="findings")
    job = relationship("Job", back_populates="findings")