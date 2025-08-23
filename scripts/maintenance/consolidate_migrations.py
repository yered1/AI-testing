#!/usr/bin/env python3
"""Consolidate all database migrations into a single initial migration"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def consolidate_migrations():
    migrations_dir = Path("orchestrator/alembic/versions")
    
    if not migrations_dir.exists():
        print("Migrations directory not found")
        return
    
    # Archive old migrations
    archive_dir = migrations_dir / "archived"
    archive_dir.mkdir(exist_ok=True)
    
    for migration in migrations_dir.glob("*.py"):
        if migration.name != "__init__.py":
            shutil.move(str(migration), str(archive_dir / migration.name))
    
    # Create consolidated migration
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    migration_file = migrations_dir / f"001_{timestamp}_initial.py"
    
    with open(migration_file, "w") as f:
        f.write('''"""Initial consolidated migration

Revision ID: 001_initial
Create Date: {}
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None

def upgrade():
    # Core tables
    op.create_table('tenants',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now())
    )
    
    op.create_table('engagements',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('tenant_id', sa.String(), sa.ForeignKey('tenants.id')),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String()),
        sa.Column('scope', sa.JSON()),
        sa.Column('status', sa.String()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), onupdate=sa.func.now())
    )
    
    # Add indexes
    op.create_index('idx_engagements_tenant', 'engagements', ['tenant_id'])
    op.create_index('idx_engagements_status', 'engagements', ['status'])

def downgrade():
    op.drop_table('engagements')
    op.drop_table('tenants')
'''.format(datetime.now()))
    
    print(f"Created consolidated migration: {migration_file}")
    print(f"Archived {len(list(archive_dir.glob('*.py')))} old migrations")

if __name__ == "__main__":
    consolidate_migrations()
