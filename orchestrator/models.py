from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Enum, JSON, ForeignKey, UniqueConstraint, Index, Boolean, DateTime, func
import enum
from .db import Base

class Role(str, enum.Enum):
    ORG_OWNER = "org_owner"
    TENANT_ADMIN = "tenant_admin"
    PROJECT_MANAGER = "project_manager"
    TEST_REQUESTER = "test_requester"
    ANALYST = "analyst"
    VIEWER = "viewer"
    AUDITOR = "auditor"
    AGENT_OPERATOR = "agent_operator"

class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)   # internal id (uuid)
    subject: Mapped[str] = mapped_column(String, unique=True)   # OIDC sub
    email: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Membership(Base):
    __tablename__ = "memberships"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[Role] = mapped_column(Enum(Role))
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("tenant_id","user_id", name="uq_member"),)

class Engagement(Base):
    __tablename__ = "engagements"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)  # network|webapp|api|mobile|code|cloud
    scope: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    Index("ix_engagements_tenant", "tenant_id")

class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    engagement_id: Mapped[str] = mapped_column(String, ForeignKey("engagements.id", ondelete="CASCADE"), index=True)
    plan_hash: Mapped[str] = mapped_column(String, index=True)
    data: Mapped[dict] = mapped_column(JSON)
    catalog_version: Mapped[str] = mapped_column(String, default="0.1.0")
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    engagement_id: Mapped[str] = mapped_column(String, ForeignKey("engagements.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("plans.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String, default="queued")
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
