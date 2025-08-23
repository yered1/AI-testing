# File: AI-testing/orchestrator/alembic/versions/0004_findings_reporting.py

- Size: 2627 bytes
- Kind: text
- SHA256: 9d9852f748f40287ec9f045e80fe0c41eec9ff5e8e752fbdc0916d1bde9c6c69

## Python Imports

```
alembic, logging, sqlalchemy
```

## Head (first 60 lines)

```
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
        sa.Column("run_id", sa.String(), sa.ForeignKey("runs.id", ondelete="CASCADE"), index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("assets", sa.JSON(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )
    op.create_index("ix_findings_run", "findings", ["run_id","created_at"])

    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("runs.id", ondelete="CASCADE"), index=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("linked_finding_id", sa.String(), sa.ForeignKey("findings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )
    op.create_index("ix_artifacts_run", "artifacts", ["run_id","created_at"])

    for tbl in ["findings","artifacts"]:
        op.execute(f'ALTER TABLE "{tbl}" ENABLE ROW LEVEL SECURITY;')
        op.execute(f"""
        CREATE POLICY {tbl}_tenant_isolation ON "{tbl}"
        USING (tenant_id::text = current_setting('app.current_tenant', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant', true));
        """)

def downgrade():
    for tbl in ["artifacts","findings"]:
        try:
            op.execute(f'DROP POLICY IF EXISTS {tbl}_tenant_isolation ON "{tbl}";')
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning('Alembic step ignored due to error: %s', e)
    op.drop_index("ix_artifacts_run", table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_index("ix_findings_run", table_name="findings")
    op.drop_table("findings")
```

