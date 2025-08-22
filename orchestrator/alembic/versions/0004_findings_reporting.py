from alembic import op
import sqlalchemy as sa

revision = "0004_findings_reporting"
down_revision = "0003_run_events"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "findings",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("engagement_id", sa.String(), sa.ForeignKey("engagements.id", ondelete="CASCADE"), index=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("runs.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(), nullable=False),  # info|low|medium|high|critical
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("owasp", sa.String(), nullable=True),
        sa.Column("cwe", sa.String(), nullable=True),
        sa.Column("cvss", sa.String(), nullable=True),
        sa.Column("affected_assets", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="open"),  # open|confirmed|accepted-risk|fixed|false-positive
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index("ix_findings_eng_sev", "findings", ["engagement_id", "severity"])

    op.create_table(
        "finding_evidence",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("finding_id", sa.String(), sa.ForeignKey("findings.id", ondelete="CASCADE"), index=True),
        sa.Column("type", sa.String(), nullable=False),  # url|text
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("engagement_id", sa.String(), sa.ForeignKey("engagements.id", ondelete="CASCADE"), index=True),
        sa.Column("format", sa.String(), nullable=False),  # md|json
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )

    # RLS
    for tbl in ["findings","finding_evidence","reports"]:
        op.execute(f'ALTER TABLE "{tbl}" ENABLE ROW LEVEL SECURITY;')
        op.execute(f'''
        CREATE POLICY {tbl}_tenant_isolation ON "{tbl}"
        USING (tenant_id::text = current_setting(''app.current_tenant'', true))
        WITH CHECK (tenant_id::text = current_setting(''app.current_tenant'', true));
        ''')

def downgrade():
    for tbl in ["reports","finding_evidence","findings"]:
        try:
            op.execute(f'DROP POLICY IF EXISTS {tbl}_tenant_isolation ON "{tbl}";')
        except Exception:
            pass
    op.drop_table("reports")
    op.drop_table("finding_evidence")
    op.drop_index("ix_findings_eng_sev", table_name="findings")
    op.drop_table("findings")
