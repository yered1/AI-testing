# Destination: patches/v2.0.0/orchestrator/alembic/env.py
# Rationale: Alembic environment setup that properly loads database URL from environment
# Supports multiple environment variable names for flexibility

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models here for autogenerate support
try:
    from orchestrator.models import Base
    target_metadata = Base.metadata
except ImportError:
    print("Warning: Could not import models. Running without metadata.")
    target_metadata = None


def get_database_url():
    """Get database URL from environment variables."""
    # Try multiple possible environment variable names
    for env_var in ['DATABASE_URL', 'DB_URL', 'DB_DSN', 'POSTGRES_URL']:
        url = os.environ.get(env_var)
        if url:
            # Handle DATABASE_URL format from some providers
            if url.startswith('postgres://'):
                url = url.replace('postgres://', 'postgresql://', 1)
            return url
    
    # Fallback to constructing from individual components
    db_user = os.environ.get('DB_USER', os.environ.get('POSTGRES_USER', 'postgres'))
    db_pass = os.environ.get('DB_PASSWORD', os.environ.get('POSTGRES_PASSWORD', 'postgres'))
    db_host = os.environ.get('DB_HOST', os.environ.get('POSTGRES_HOST', 'localhost'))
    db_port = os.environ.get('DB_PORT', os.environ.get('POSTGRES_PORT', '5432'))
    db_name = os.environ.get('DB_NAME', os.environ.get('POSTGRES_DB', 'orchestrator'))
    
    return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Override the sqlalchemy.url with environment variable
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()