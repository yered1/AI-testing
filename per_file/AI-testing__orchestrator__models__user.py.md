# File: AI-testing/orchestrator/models/user.py

- Size: 1013 bytes
- Kind: text
- SHA256: 9f26e38cefba495b2b44a4be997d7304043d3c12d380ed629332d781cfaa89c8

## Python Imports

```
base, sqlalchemy, uuid
```

## Head (first 60 lines)

```
# ============================================
# orchestrator/models/user.py
"""User model with authentication"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False)
    password_hash = Column(String)
    role = Column(String, default="user")  # admin, user, viewer
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", backref="users")
```

