# File: AI-testing/orchestrator/alembic/versions/0006_brain_autoplan.py

- Size: 2611 bytes
- Kind: text
- SHA256: b45f1d04ff94a45334147524be79734decfcbd9d8cb23eca79dbf66cda09f637

## Python Imports

```
alembic, logging, sqlalchemy
```

## Head (first 60 lines)

```
from alembic import op
import sqlalchemy as sa

revision = "0006_brain_autoplan"
down_revision = "0005_agents_jobs"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "brain_feedback",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("engagement_id", sa.String(), sa.ForeignKey("engagements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("plan_id", sa.String(), sa.ForeignKey("plans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )
    op.create_index("ix_brain_feedback_tenant", "brain_feedback", ["tenant_id","created_at"])

    op.create_table(
        "brain_logs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("engagement_id", sa.String(), sa.ForeignKey("engagements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("filtered_tests", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )

    for tbl in ["brain_feedback","brain_logs"]:
        op.execute(f'ALTER TABLE "{tbl}" ENABLE ROW LEVEL SECURITY;')
        op.execute(f"""
        CREATE POLICY {tbl}_tenant_isolation ON "{tbl}"
        USING (tenant_id::text = current_setting('app.current_tenant', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant', true));
        """)

def downgrade():
    for tbl in ["brain_logs","brain_feedback"]:
        try:
            op.execute(f'DROP POLICY IF EXISTS {tbl}_tenant_isolation ON "{tbl}";')
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning('Alembic step ignored due to error: %s', e)
    op.drop_table("brain_logs")
    op.drop_index("ix_brain_feedback_tenant", table_name="brain_feedback")
    op.drop_table("brain_feedback")
```

