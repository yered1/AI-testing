# File: AI-testing/orchestrator/alembic/versions/0008_findings_enhanced.py

- Size: 5013 bytes
- Kind: text
- SHA256: 89c5b00ce49f3226c3c3bbc4867f5a73fc1631d2d061771d3728a13a934143ed

## Python Imports

```
alembic, sqlalchemy
```

## Head (first 60 lines)

```
"""Enhanced findings table with vulnerability tracking

Revision ID: 0008_findings_enhanced
Revises: 0007_brain_traces
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0008_findings_enhanced'
down_revision = '0007_brain_traces'
branch_labels = None
depends_on = None


def upgrade():
    # Create findings table with enhanced fields
    op.create_table('findings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('engagement_id', sa.String(), nullable=False),
        sa.Column('job_id', sa.String(), nullable=True),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('affected_hosts', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('affected_urls', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('cve_ids', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('cwe_ids', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('owasp_category', sa.String(), nullable=True),
        sa.Column('cvss_vector', sa.String(), nullable=True),
        sa.Column('cvss_score', sa.Float(), nullable=True),
        sa.Column('remediation', sa.Text(), nullable=True),
        sa.Column('references', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('false_positive', sa.Boolean(), nullable=False, default=False),
        sa.Column('duplicate_of', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='open'),
        sa.Column('hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('ix_findings_tenant_id', 'findings', ['tenant_id'])
    op.create_index('ix_findings_run_id', 'findings', ['run_id'])
    op.create_index('ix_findings_engagement_id', 'findings', ['engagement_id'])
    op.create_index('ix_findings_severity', 'findings', ['severity'])
    op.create_index('ix_findings_category', 'findings', ['category'])
    op.create_index('ix_findings_hash', 'findings', ['hash'])
    op.create_index('ix_findings_status', 'findings', ['status'])
    op.create_index('ix_findings_created_at', 'findings', ['created_at'])
    
```

## Tail (last 60 lines)

```
    )
    
    # Create indexes for performance
    op.create_index('ix_findings_tenant_id', 'findings', ['tenant_id'])
    op.create_index('ix_findings_run_id', 'findings', ['run_id'])
    op.create_index('ix_findings_engagement_id', 'findings', ['engagement_id'])
    op.create_index('ix_findings_severity', 'findings', ['severity'])
    op.create_index('ix_findings_category', 'findings', ['category'])
    op.create_index('ix_findings_hash', 'findings', ['hash'])
    op.create_index('ix_findings_status', 'findings', ['status'])
    op.create_index('ix_findings_created_at', 'findings', ['created_at'])
    
    # Add foreign key constraints
    op.create_foreign_key('fk_findings_run', 'findings', 'runs', ['run_id'], ['id'])
    op.create_foreign_key('fk_findings_engagement', 'findings', 'engagements', ['engagement_id'], ['id'])
    op.create_foreign_key('fk_findings_job', 'findings', 'jobs', ['job_id'], ['id'])
    op.create_foreign_key('fk_findings_agent', 'findings', 'agents', ['agent_id'], ['id'])
    op.create_foreign_key('fk_findings_duplicate', 'findings', 'findings', ['duplicate_of'], ['id'])
    
    # Enable Row Level Security
    op.execute("ALTER TABLE findings ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policy for tenant isolation
    op.execute("""
        CREATE POLICY findings_tenant_isolation ON findings
        FOR ALL
        USING (tenant_id = current_setting('app.tenant_id', true))
    """)
    
    # Create finding_comments table for collaboration
    op.create_table('finding_comments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('finding_id', sa.String(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_finding_comments_finding_id', 'finding_comments', ['finding_id'])
    op.create_foreign_key('fk_finding_comments_finding', 'finding_comments', 'findings', ['finding_id'], ['id'])
    
    # Enable RLS on comments
    op.execute("ALTER TABLE finding_comments ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY finding_comments_tenant_isolation ON finding_comments
        FOR ALL
        USING (tenant_id = current_setting('app.tenant_id', true))
    """)


def downgrade():
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS finding_comments_tenant_isolation ON finding_comments")
    op.execute("DROP POLICY IF EXISTS findings_tenant_isolation ON findings")
    
    # Drop tables
    op.drop_table('finding_comments')
    op.drop_table('findings')
```

