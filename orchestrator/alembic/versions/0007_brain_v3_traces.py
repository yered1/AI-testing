"""brain v3 traces table

Revision ID: 0007_brain_v3_traces
Revises: 0006
Create Date: 2025-08-23 00:45:53
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0007_brain_v3_traces'
down_revision = '0006'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('brain_traces',
        sa.Column('id', sa.String(length=32), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('engagement_id', sa.String(length=32), nullable=False, index=True),
        sa.Column('provider', sa.String(length=64), nullable=False),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    # Enable RLS tenant isolation
    op.execute("ALTER TABLE brain_traces ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY brain_traces_tenant_isolation ON brain_traces
        USING (tenant_id = current_setting('app.current_tenant', true))
        WITH CHECK (tenant_id = current_setting('app.current_tenant', true))
    """)

def downgrade():
    op.drop_table('brain_traces')
