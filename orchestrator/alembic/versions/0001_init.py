# Destination: patches/v2.0.0/orchestrator/alembic/versions/0001_init.py
# Rationale: Create core database tables for the orchestration platform
# This migration establishes the foundational schema

"""Initial migration - core tables

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create core tables for the orchestration platform."""
    
    # Create tenants table
    op.create_table('tenants',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index('ix_tenants_slug', 'tenants', ['slug'])
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_username', 'users', ['username'])
    
    # Create memberships table (user-tenant relationships)
    op.create_table('memberships',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant')
    )
    op.create_index('ix_memberships_user_id', 'memberships', ['user_id'])
    op.create_index('ix_memberships_tenant_id', 'memberships', ['tenant_id'])
    
    # Create engagements table
    op.create_table('engagements',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scope', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_engagements_tenant_id', 'engagements', ['tenant_id'])
    op.create_index('ix_engagements_status', 'engagements', ['status'])
    
    # Create plans table
    op.create_table('plans',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('engagement_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('plan_type', sa.String(50), nullable=False, server_default='manual'),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['engagement_id'], ['engagements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_plans_engagement_id', 'plans', ['engagement_id'])
    
    # Create runs table
    op.create_table('runs',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('plan_id', sa.UUID(), nullable=False),
        sa.Column('run_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('approval_status', sa.String(50), nullable=True),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id', 'run_number', name='uq_plan_run_number')
    )
    op.create_index('ix_runs_plan_id', 'runs', ['plan_id'])
    op.create_index('ix_runs_status', 'runs', ['status'])
    
    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_id', sa.UUID(), nullable=False),
        sa.Column('job_type', sa.String(100), nullable=False),
        sa.Column('job_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('agent_id', sa.UUID(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_jobs_run_id', 'jobs', ['run_id'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    op.create_index('ix_jobs_agent_id', 'jobs', ['agent_id'])
    
    # Create agents table
    op.create_table('agents',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('agent_type', sa.String(100), nullable=False),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('capabilities', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='offline'),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.Column('api_token', sa.String(255), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_agents_name', 'agents', ['name'])
    op.create_index('ix_agents_status', 'agents', ['status'])
    
    # Create run_events table
    op.create_table('run_events',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False, server_default='info'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_run_events_run_id', 'run_events', ['run_id'])
    op.create_index('ix_run_events_job_id', 'run_events', ['job_id'])
    op.create_index('ix_run_events_event_type', 'run_events', ['event_type'])
    
    # Create artifacts table
    op.create_table('artifacts',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=True),
        sa.Column('label', sa.String(255), nullable=False),
        sa.Column('kind', sa.String(100), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('checksum', sa.String(255), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_artifacts_run_id', 'artifacts', ['run_id'])
    op.create_index('ix_artifacts_job_id', 'artifacts', ['job_id'])
    op.create_index('ix_artifacts_kind', 'artifacts', ['kind'])
    
    # Create findings table (new for v2.0.0)
    op.create_table('findings',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=True),
        sa.Column('finding_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('remediation', sa.Text(), nullable=True),
        sa.Column('false_positive', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('cvss_score', sa.Float(), nullable=True),
        sa.Column('cve_ids', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['run_id'], ['runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_findings_run_id', 'findings', ['run_id'])
    op.create_index('ix_findings_severity', 'findings', ['severity'])
    op.create_index('ix_findings_status', 'findings', ['status'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('findings')
    op.drop_table('artifacts')
    op.drop_table('run_events')
    op.drop_table('jobs')
    op.drop_table('runs')
    op.drop_table('plans')
    op.drop_table('engagements')
    op.drop_table('agents')
    op.drop_table('memberships')
    op.drop_table('users')
    op.drop_table('tenants')