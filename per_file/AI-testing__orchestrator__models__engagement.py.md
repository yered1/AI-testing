# File: AI-testing/orchestrator/models/engagement.py

- Size: 1599 bytes
- Kind: text
- SHA256: 033eb6e873c6fae1fa2bb760307958c2f0c1f69d4d548525b8b734eb503b6f37

## Python Imports

```
base, enum, sqlalchemy, uuid
```

## Head (first 60 lines)

```
# ============================================
# orchestrator/models/engagement.py
"""Engagement model for test projects"""

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid
import enum

class EngagementType(enum.Enum):
    WEB_APPLICATION = "web_application"
    API = "api"
    MOBILE = "mobile"
    NETWORK = "network"
    CLOUD = "cloud"
    CODE = "code"

class EngagementStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class Engagement(Base):
    __tablename__ = "engagements"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    type = Column(Enum(EngagementType), nullable=False)
    status = Column(Enum(EngagementStatus), default=EngagementStatus.DRAFT)
    scope = Column(JSON, nullable=False)  # {"targets": [], "exclude": []}
    metadata = Column(JSON, default=dict)
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", backref="engagements")
    creator = relationship("User", backref="engagements")
    plans = relationship("Plan", back_populates="engagement", cascade="all, delete-orphan")
```

