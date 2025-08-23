#!/bin/bash
# Initialize the AI-testing project with all necessary files

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "========================================"
echo "Initializing AI Pentest Platform"
echo "========================================"

# 1. Create directory structure
echo "Creating directory structure..."
mkdir -p "${PROJECT_ROOT}/orchestrator/catalog/tests"
mkdir -p "${PROJECT_ROOT}/orchestrator/catalog/packs"
mkdir -p "${PROJECT_ROOT}/orchestrator/routers"
mkdir -p "${PROJECT_ROOT}/orchestrator/brain/providers"
mkdir -p "${PROJECT_ROOT}/orchestrator/alembic/versions"
mkdir -p "${PROJECT_ROOT}/orchestrator/models"
mkdir -p "${PROJECT_ROOT}/orchestrator/agent_sdk"
mkdir -p "${PROJECT_ROOT}/policies"
mkdir -p "${PROJECT_ROOT}/agents/dev_agent"
mkdir -p "${PROJECT_ROOT}/infra"

# 2. Create catalog files if they don't exist
if [ ! -f "${PROJECT_ROOT}/orchestrator/catalog/tests/tests.json" ]; then
    echo "Creating catalog files..."
    cat > "${PROJECT_ROOT}/orchestrator/catalog/tests/tests.json" << 'EOF'
{
  "network_scan": {
    "id": "network_scan",
    "name": "Network Scan",
    "description": "Basic network scanning",
    "category": "Network",
    "agent_type": "network",
    "risk_level": "low",
    "requires_approval": false
  },
  "web_scan": {
    "id": "web_scan",
    "name": "Web Application Scan",
    "description": "Web application scanning",
    "category": "Web",
    "agent_type": "web",
    "risk_level": "low",
    "requires_approval": false
  }
}
EOF

    cat > "${PROJECT_ROOT}/orchestrator/catalog/packs/packs.json" << 'EOF'
{
  "basic": {
    "id": "basic",
    "name": "Basic Security Assessment",
    "description": "Basic security testing",
    "tests": ["network_scan", "web_scan"]
  }
}
EOF
fi

# 3. Create minimal OPA policy
if [ ! -f "${PROJECT_ROOT}/policies/policy.rego" ]; then
    echo "Creating OPA policy..."
    cat > "${PROJECT_ROOT}/policies/policy.rego" << 'EOF'
package authz

default allow = true

# Basic policy - allow all for now
allow {
    true
}

# Tenant isolation
tenant_allowed {
    input.tenant_id == data.current_tenant
}
EOF
fi

# 4. Create __init__.py files
echo "Creating Python package files..."
touch "${PROJECT_ROOT}/orchestrator/__init__.py"
touch "${PROJECT_ROOT}/orchestrator/routers/__init__.py"
touch "${PROJECT_ROOT}/orchestrator/brain/__init__.py"
touch "${PROJECT_ROOT}/orchestrator/brain/providers/__init__.py"
touch "${PROJECT_ROOT}/orchestrator/models/__init__.py"
touch "${PROJECT_ROOT}/orchestrator/agent_sdk/__init__.py"

# 5. Create basic database models
if [ ! -f "${PROJECT_ROOT}/orchestrator/models.py" ]; then
    cat > "${PROJECT_ROOT}/orchestrator/models.py" << 'EOF'
"""Database models for AI Pentest Platform"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Tenant(Base):
    __tablename__ = 'tenants'
    
    id = Column(String, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Agent(Base):
    __tablename__ = 'agents'
    
    id = Column(String, primary_key=True)
    tenant_id = Column(String)
    name = Column(String)
    type = Column(String)
    status = Column(String)
    capabilities = Column(JSON)
    last_heartbeat = Column(DateTime)

class Engagement(Base):
    __tablename__ = 'engagements'
    
    id = Column(String, primary_key=True)
    tenant_id = Column(String)
    name = Column(String)
    type = Column(String)
    scope = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Run(Base):
    __tablename__ = 'runs'
    
    id = Column(String, primary_key=True)
    engagement_id = Column(String)
    status = Column(String)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(String, primary_key=True)
    run_id = Column(String)
    agent_id = Column(String)
    type = Column(String)
    status = Column(String)
    command = Column(String)
    params = Column(JSON)
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
EOF
fi

# 6. Create database configuration
if [ ! -f "${PROJECT_ROOT}/orchestrator/database.py" ]; then
    cat > "${PROJECT_ROOT}/orchestrator/database.py" << 'EOF'
"""Database configuration"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://pentest:pentest@localhost:5432/pentest")

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Create async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

# Create async session
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
EOF
fi

# 7. Create auth module
if [ ! -f "${PROJECT_ROOT}/orchestrator/auth.py" ]; then
    cat > "${PROJECT_ROOT}/orchestrator/auth.py" << 'EOF'
"""Authentication module"""
from fastapi import Header, HTTPException

async def get_current_tenant(
    x_tenant_id: str = Header(None, alias="X-Tenant-Id")
) -> str:
    """Get current tenant from header"""
    if not x_tenant_id:
        x_tenant_id = "t_demo"  # Default for development
    return x_tenant_id

async def get_current_user(
    x_dev_user: str = Header(None, alias="X-Dev-User"),
    x_dev_email: str = Header(None, alias="X-Dev-Email")
) -> dict:
    """Get current user from headers"""
    return {
        "username": x_dev_user or "dev",
        "email": x_dev_email or "dev@example.com"
    }
EOF
fi

# 8. Create Alembic configuration
if [ ! -f "${PROJECT_ROOT}/orchestrator/alembic.ini" ]; then
    echo "Creating Alembic configuration..."
    cat > "${PROJECT_ROOT}/orchestrator/alembic.ini" << 'EOF'
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://pentest:pentest@db:5432/pentest

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

    # Create alembic env.py
    mkdir -p "${PROJECT_ROOT}/orchestrator/alembic"
    cat > "${PROJECT_ROOT}/orchestrator/alembic/env.py" << 'EOF'
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = os.environ.get('DATABASE_URL', configuration['sqlalchemy.url'])
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

    # Create initial migration
    cat > "${PROJECT_ROOT}/orchestrator/alembic/versions/001_initial.py" << 'EOF'
"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create tenants table
    op.create_table('tenants',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create agents table
    op.create_table('agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('capabilities', sa.JSON(), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create engagements table
    op.create_table('engagements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('scope', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create runs table
    op.create_table('runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('engagement_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=True),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('command', sa.String(), nullable=True),
        sa.Column('params', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('jobs')
    op.drop_table('runs')
    op.drop_table('engagements')
    op.drop_table('agents')
    op.drop_table('tenants')
EOF
fi

# 9. Make scripts executable
chmod +x "${PROJECT_ROOT}/scripts/"*.sh 2>/dev/null || true

echo ""
echo "========================================"
echo "Initialization Complete!"
echo "========================================"
echo ""
echo "Project structure created successfully!"
echo ""
echo "Next steps:"
echo "1. Commit these files to your repository:"
echo "   git add ."
echo "   git commit -m 'fix: Add missing project files and fix CI'"
echo "   git push"
echo ""
echo "2. Start the services locally:"
echo "   docker compose -f infra/docker-compose.v2.yml up -d"
echo ""
echo "3. Run migrations:"
echo "   docker compose -f infra/docker-compose.v2.yml exec orchestrator alembic upgrade head"
echo ""
echo "The CI should now pass!"