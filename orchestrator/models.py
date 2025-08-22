from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, JSON, ForeignKey, Enum, DateTime, func
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
    id: Mapped[str] = mapped_column(String, primary_key=True)
    subject: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Membership(Base):
    __tablename__ = "memberships"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped["Role"] = mapped_column(Enum(Role))
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Engagement(Base):
    __tablename__ = "engagements"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    scope: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id", ondelete="CASCADE"))
    engagement_id: Mapped[str] = mapped_column(String, ForeignKey("engagements.id", ondelete="CASCADE"))
    plan_hash: Mapped[str] = mapped_column(String)
    data: Mapped[dict] = mapped_column(JSON)
    catalog_version: Mapped[str] = mapped_column(String, default="0.1.0")
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, ForeignKey("tenants.id", ondelete="CASCADE"))
    engagement_id: Mapped[str] = mapped_column(String, ForeignKey("engagements.id", ondelete="CASCADE"))
    plan_id: Mapped[str] = mapped_column(String, ForeignKey("plans.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String, default="queued")
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
