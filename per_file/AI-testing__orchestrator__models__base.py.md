# File: AI-testing/orchestrator/models/base.py

- Size: 1019 bytes
- Kind: text
- SHA256: 83174cabe11de767d140c10874b8fc21fa8e172ed8846935cef5d669d62ca30c

## Python Imports

```
contextlib, os, sqlalchemy, typing
```

## Head (first 60 lines)

```
# ============================================
# orchestrator/models/base.py
"""Base database configuration"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/ai_testing")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

metadata = MetaData()
Base = declarative_base(metadata=metadata)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Database session context manager"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database with tables"""
    Base.metadata.create_all(bind=engine)
```

