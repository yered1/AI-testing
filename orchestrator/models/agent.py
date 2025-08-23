# ============================================
# orchestrator/models/agent.py
"""Agent and agent token models"""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid
import enum
import secrets

class AgentType(enum.Enum):
    ZAP = "zap"
    NUCLEI = "nuclei"
    SEMGREP = "semgrep"
    NMAP = "nmap"
    SQLMAP = "sqlmap"
    MOBILE = "mobile"
    CUSTOM = "custom"

class AgentStatus(enum.Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"
    ERROR = "error"

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(Enum(AgentType), nullable=False)
    status = Column(Enum(AgentStatus), default=AgentStatus.OFFLINE)
    version = Column(String)
    capabilities = Column(JSON, default=list)  # List of test IDs it can run
    metadata = Column(JSON, default=dict)
    last_heartbeat = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tenant = relationship("Tenant", backref="agents")
    jobs = relationship("Job", back_populates="agent")
    tokens = relationship("AgentToken", back_populates="agent", cascade="all, delete-orphan")

class AgentToken(Base):
    __tablename__ = "agent_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    token_hash = Column(String, nullable=False, unique=True)
    name = Column(String)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="tokens")
    
    @staticmethod
    def generate_token():
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)
