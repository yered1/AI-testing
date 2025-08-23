# File: AI-testing/orchestrator/alembic/env.py

- Size: 1471 bytes
- Kind: text
- SHA256: 91769910851849af2027b6eea1282454430d086fd755f9c67036f11a8e167378

## Python Imports

```
alembic, logging, orchestrator, os, sqlalchemy, sys
```

## Head (first 60 lines)

```
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os, sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
from orchestrator.db import Base
from orchestrator.models import *  # noqa

config = context.config
section = config.config_ini_section
if "DATABASE_URL" in os.environ:
    config.set_section_option(section, "sqlalchemy.url", os.environ["DATABASE_URL"])

if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception as e:
        import sys
        print(f"[alembic] logging config load skipped: {e}", file=sys.stderr)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

