# File: AI-testing/orchestrator/db.py

- Size: 462 bytes
- Kind: text
- SHA256: f24419a2dd200825066fcd5e6dda62324dafcf8d85b1305ce40ced64dd0695b2

## Python Imports

```
settings, sqlalchemy
```

## Head (first 60 lines)

```
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, scoped_session
from .settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True))

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

