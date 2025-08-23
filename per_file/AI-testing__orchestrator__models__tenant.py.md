# File: AI-testing/orchestrator/models/tenant.py

- Size: 788 bytes
- Kind: text
- SHA256: 531aaf2e6cdf8b5fe4ba694723c660db07ef5349c7ddb0d2f5d721610904f4da

## Python Imports

```
base, sqlalchemy, uuid
```

## Head (first 60 lines)

```
# ============================================
# orchestrator/models/tenant.py
"""Tenant model for multi-tenancy"""

from sqlalchemy import Column, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from .base import Base
import uuid

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    display_name = Column(String)
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    max_users = Column(String, default=10)
    max_agents = Column(String, default=5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

