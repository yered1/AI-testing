from alembic import op
import sqlalchemy as sa

revision = "0004_findings_reporting"
down_revision = "0003_run_events"
branch_labels = None
depends_on = None

def upgrade():
    severity_enum = sa.Enum("info","low","medium","high","critical", name="severity")
    severity_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "findings",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("runs.id", ondelete="CASCADE"), index=True),
        sa.Column("engagement_id", sa.String(), sa.ForeignKey("engagements.id", ondelete="CASCADE"), index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("severity", severity_enum, nullable=False, server_default="low"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assets", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("cvss_vector", sa.String(), nullable=True),
        sa.Column("cvss_score", sa.Float(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )
    op.create_index("ix_findings_run", "findings", ["run_id"])
    op.create_index("ix_findings_sev", "findings", ["severity"])
    op.create_index("ix_findings_status", "findings", ["status"])

    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("runs.id", ondelete="CASCADE"), index=True),
        sa.Column("finding_id", sa.String(), sa.ForeignKey("findings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", sa.String(), nullable=False, server_default="file"),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )
    op.create_index("ix_artifacts_run", "artifacts", ["run_id"])

    op.create_table(
        "evidence",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("runs.id", ondelete="CASCADE"), index=True),
        sa.Column("finding_id", sa.String(), sa.ForeignKey("findings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("etype", sa.String(), nullable=False, server_default="note"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )

    for tbl in ["findings","artifacts","evidence"]:
        op.execute(f'ALTER TABLE "{tbl}" ENABLE ROW LEVEL SECURITY;')
        op.execute(f'''
        CREATE POLICY {tbl}_tenant_isolation ON "{tbl}"
        USING (tenant_id::text = current_setting(''app.current_tenant'', true))
        WITH CHECK (tenant_id::text = current_setting(''app.current_tenant'', true));
        ''')

def downgrade():
    for tbl in ["evidence","artifacts","findings"]:
        try:
            op.execute(f'DROP POLICY IF EXISTS {tbl}_tenant_isolation ON "{tbl}";')
        except Exception:
            pass
    op.drop_table("evidence")
    op.drop_index("ix_artifacts_run", table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_index("ix_findings_status", table_name="findings")
    op.drop_index("ix_findings_sev", table_name="findings")
    op.drop_index("ix_findings_run", table_name="findings")
    op.drop_table("findings")
