from alembic import op
import sqlalchemy as sa

revision = "0003_run_events"
down_revision = "0002_quotas_approvals"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "run_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("runs.id", ondelete="CASCADE"), index=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), index=True)
    )
    op.create_index("ix_run_events_run_time", "run_events", ["run_id","created_at"])

    # RLS policies using tenant GUC
    op.execute('ALTER TABLE "run_events" ENABLE ROW LEVEL SECURITY;')
    op.execute('''
    CREATE POLICY run_events_tenant_isolation ON "run_events"
    USING (tenant_id::text = current_setting(''app.current_tenant'', true))
    WITH CHECK (tenant_id::text = current_setting(''app.current_tenant'', true));
    ''')

def downgrade():
    try:
        op.execute('DROP POLICY IF EXISTS run_events_tenant_isolation ON "run_events";')
    except Exception:
        pass
    op.drop_index("ix_run_events_run_time", table_name="run_events")
    op.drop_table("run_events")
