# File: AI-testing/orchestrator/alembic/versions/0002_quotas_approvals.py

- Size: 3090 bytes
- Kind: text
- SHA256: 26d10ac6080274676cf28f037404b552d662a7a92bebd34e1b69c1248c1779e3

## Python Imports

```
alembic, sqlalchemy
```

## Head (first 60 lines)

```
from alembic import op
import sqlalchemy as sa

revision = "0002_quotas_approvals"
down_revision = "0001_init"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "quotas",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("monthly_budget", sa.Integer(), nullable=False),
        sa.Column("per_plan_cap", sa.Integer(), nullable=False),
        sa.Column("month_key", sa.String(), nullable=False),  # e.g., 2025-08
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )
    op.create_index("ix_quotas_tenant_month", "quotas", ["tenant_id","month_key"], unique=True)

    op.create_table(
        "quota_usage",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("engagement_id", sa.String(), sa.ForeignKey("engagements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column("month_key", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )

    op.create_table(
        "approvals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("engagement_id", sa.String(), sa.ForeignKey("engagements.id", ondelete="CASCADE"), index=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),  # pending|approved|denied
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("decided_by", sa.String(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True)
    )

    # RLS enablement (reuse tenant GUC)
    for tbl in ["quotas","quota_usage","approvals"]:
        op.execute(f'ALTER TABLE "{tbl}" ENABLE ROW LEVEL SECURITY;')
        op.execute(f'''
        CREATE POLICY {tbl}_tenant_isolation ON "{tbl}"
        USING (tenant_id::text = current_setting(''app.current_tenant'', true))
        WITH CHECK (tenant_id::text = current_setting(''app.current_tenant'', true));
        ''')

def downgrade():
    for tbl in ["approvals","quota_usage","quotas"]:
        try:
            op.execute(f'DROP POLICY IF EXISTS {tbl}_tenant_isolation ON "{tbl}";')
        except Exception:
            pass
    op.drop_table("approvals")
```

## Tail (last 60 lines)

```
revision = "0002_quotas_approvals"
down_revision = "0001_init"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "quotas",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("monthly_budget", sa.Integer(), nullable=False),
        sa.Column("per_plan_cap", sa.Integer(), nullable=False),
        sa.Column("month_key", sa.String(), nullable=False),  # e.g., 2025-08
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )
    op.create_index("ix_quotas_tenant_month", "quotas", ["tenant_id","month_key"], unique=True)

    op.create_table(
        "quota_usage",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("engagement_id", sa.String(), sa.ForeignKey("engagements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column("month_key", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"))
    )

    op.create_table(
        "approvals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), index=True),
        sa.Column("engagement_id", sa.String(), sa.ForeignKey("engagements.id", ondelete="CASCADE"), index=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),  # pending|approved|denied
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("decided_by", sa.String(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True)
    )

    # RLS enablement (reuse tenant GUC)
    for tbl in ["quotas","quota_usage","approvals"]:
        op.execute(f'ALTER TABLE "{tbl}" ENABLE ROW LEVEL SECURITY;')
        op.execute(f'''
        CREATE POLICY {tbl}_tenant_isolation ON "{tbl}"
        USING (tenant_id::text = current_setting(''app.current_tenant'', true))
        WITH CHECK (tenant_id::text = current_setting(''app.current_tenant'', true));
        ''')

def downgrade():
    for tbl in ["approvals","quota_usage","quotas"]:
        try:
            op.execute(f'DROP POLICY IF EXISTS {tbl}_tenant_isolation ON "{tbl}";')
        except Exception:
            pass
    op.drop_table("approvals")
    op.drop_table("quota_usage")
    op.drop_index("ix_quotas_tenant_month", table_name="quotas")
    op.drop_table("quotas")
```

