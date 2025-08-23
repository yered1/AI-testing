#!/usr/bin/env python3
"""Consolidate database migrations into a single initial migration"""

import os
import sys
import re
from pathlib import Path

def consolidate_migrations():
    """Consolidate all migrations into a single file"""
    
    migrations_dir = Path("orchestrator/alembic/versions")
    if not migrations_dir.exists():
        print("Migrations directory not found")
        return
    
    # Read all migration files
    migrations = sorted(migrations_dir.glob("*.py"))
    
    if not migrations:
        print("No migrations found")
        return
    
    # Create consolidated migration
    consolidated = """
\"\"\"Consolidated initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

\"\"\"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create tables
    
    # Tenants table
    op.create_table('tenants',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Engagements table
    op.create_table('engagements',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('scope', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Plans table
    op.create_table('plans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('engagement_id', sa.String(), nullable=False),
        sa.Column('tests', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Runs table
    op.create_table('runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('plan_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Jobs table
    op.create_table('jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('agent_type', sa.String(), nullable=True),
        sa.Column('adapter', sa.String(), nullable=True),
        sa.Column('params', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Agents table
    op.create_table('agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('token_hash', sa.String(), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Findings table
    op.create_table('findings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=True),
        sa.Column('severity', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Artifacts table
    op.create_table('artifacts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Brain traces table
    op.create_table('brain_traces',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('engagement_id', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=True),
        sa.Column('operation', sa.String(), nullable=True),
        sa.Column('input', sa.JSON(), nullable=True),
        sa.Column('output', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_engagements_tenant', 'engagements', ['tenant_id'])
    op.create_index('idx_jobs_run', 'jobs', ['run_id'])
    op.create_index('idx_jobs_status', 'jobs', ['status'])
    op.create_index('idx_findings_run', 'findings', ['run_id'])
    op.create_index('idx_artifacts_run', 'artifacts', ['run_id'])
    op.create_index('idx_agents_tenant', 'agents', ['tenant_id'])
    op.create_index('idx_brain_traces_tenant', 'brain_traces', ['tenant_id'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_brain_traces_tenant')
    op.drop_index('idx_agents_tenant')
    op.drop_index('idx_artifacts_run')
    op.drop_index('idx_findings_run')
    op.drop_index('idx_jobs_status')
    op.drop_index('idx_jobs_run')
    op.drop_index('idx_engagements_tenant')
    
    # Drop tables
    op.drop_table('brain_traces')
    op.drop_table('artifacts')
    op.drop_table('findings')
    op.drop_table('agents')
    op.drop_table('jobs')
    op.drop_table('runs')
    op.drop_table('plans')
    op.drop_table('engagements')
    op.drop_table('tenants')
"""
    
    # Write consolidated migration
    output_file = migrations_dir / "001_initial.py"
    output_file.write_text(consolidated)
    
    # Archive old migrations
    archive_dir = migrations_dir / "archived"
    archive_dir.mkdir(exist_ok=True)
    
    for migration in migrations:
        if migration.name != "001_initial.py":
            migration.rename(archive_dir / migration.name)
    
    print(f"Consolidated {len(migrations)} migrations into 001_initial.py")
    print(f"Old migrations archived in {archive_dir}")

if __name__ == "__main__":
    consolidate_migrations()
