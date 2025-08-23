import os
import sys
from pathlib import Path
from importlib.machinery import SourceFileLoader
from types import ModuleType

from alembic import context
from sqlalchemy import engine_from_config, pool

# this config object provides access to the values within the .ini file in use.
config = context.config

# Resolve /app/orchestrator for db.py dynamically based on this file location
HERE = Path(__file__).resolve()
ORCH_DIR = HERE.parent.parent  # .../orchestrator
APP_DIR = ORCH_DIR.parent      # .../app

# Ensure /app in sys.path so type imports in models that reference package names won't explode
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

def _load_db_base():
    # Load db.py as a module without importing orchestrator.__init__
    db_path = ORCH_DIR / "db.py"
    if not db_path.exists():
        raise RuntimeError(f"Expected db.py at {db_path}, cannot load Base metadata for Alembic")
    loader = SourceFileLoader("orchestrator_db_ci", str(db_path))
    mod = ModuleType(loader.name)
    loader.exec_module(mod)
    Base = getattr(mod, "Base", None)
    if Base is None:
        raise RuntimeError("orchestrator.db.Base not found")
    return Base

Base = _load_db_base()
target_metadata = Base.metadata

def get_url():
    for k in ("DATABASE_URL","DB_URL","DB_DSN","SQLALCHEMY_DATABASE_URI"):
        v = os.getenv(k)
        if v: return v
    return config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    ini_section = config.get_section(config.config_ini_section) or {}
    ini_section["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
