# ============================================
# orchestrator/models/report.py
"""Report generation model"""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid
import enum

class ReportFormat(enum.Enum):
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    MARKDOWN = "markdown"
    EXCEL = "excel"

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("runs.id"), nullable=False)
    format = Column(Enum(ReportFormat), nullable=False)
    name = Column(String, nullable=False)
    path = Column(String)  # Storage path
    template = Column(String)  # Template used
    metadata = Column(JSON, default=dict)
    generated_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    generator = relationship("User")