from alembic import op
import sqlalchemy as sa

revision = "0005_agents_jobs"
down_revision = "0004_findings_reporting"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "agent_tokens",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("created_by", sa.String(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index("ix_agent_tokens_tenant", "agent_tokens", ["tenant_id"])

    op.create_table(
        "agents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False, server_default="cross_platform"),
        sa.Column("status", sa.String(), nullable=False, server_default="online"),
        sa.Column("agent_key_hash", sa.String(), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )
    op.create_index("ix_agents_tenant", "agents", ["tenant_id"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("runs.id", ondelete="CASCADE"), index=True),
        sa.Column("plan_id", sa.String(), sa.ForeignKey("plans.id", ondelete="CASCADE"), index=True),
        sa.Column("engagement_id", sa.String(), sa.ForeignKey("engagements.id", ondelete="CASCADE"), index=True),
        sa.Column("step_id", sa.String(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("adapter", sa.String(), nullable=False),
        sa.Column("params", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="queued"),
        sa.Column("leased_by", sa.String(), sa.ForeignKey("agents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )
    op.create_index("ix_jobs_run_order", "jobs", ["run_id","order_index"])

    op.create_table(
        "job_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("job_id", sa.String(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), index=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )
    op.create_index("ix_job_events_job_time", "job_events", ["job_id","created_at"])

    for tbl in ["agent_tokens","agents","jobs","job_events"]:
        op.execute(f'ALTER TABLE "{tbl}" ENABLE ROW LEVEL SECURITY;')
        op.execute(f"""
        CREATE POLICY {tbl}_tenant_isolation ON "{tbl}"
        USING (tenant_id::text = current_setting('app.current_tenant', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant', true));
        """)

def downgrade():
    for tbl in ["job_events","jobs","agents","agent_tokens"]:
        try:
            op.execute(f'DROP POLICY IF EXISTS {tbl}_tenant_isolation ON "{tbl}";')
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning('Alembic step ignored due to error: %s', e)
    op.drop_index("ix_job_events_job_time", table_name="job_events")
    op.drop_table("job_events")
    op.drop_index("ix_jobs_run_order", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_agents_tenant", table_name="agents")
    op.drop_table("agents")
    op.drop_index("ix_agent_tokens_tenant", table_name="agent_tokens")
    op.drop_table("agent_tokens")
