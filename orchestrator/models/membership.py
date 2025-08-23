# Destination: patches/v2.0.0/orchestrator/models/membership.py
# Rationale: Add missing Membership model and Role enum for auth/tenancy
# Required by auth.py and tenancy.py

from enum import Enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class Role(str, Enum):
    """User roles within a tenant."""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    MEMBER = "member"  # Default role
    
    @classmethod
    def has_permission(cls, role: str, required: str) -> bool:
        """Check if a role has permission for required level."""
        hierarchy = {
            cls.VIEWER: 0,
            cls.MEMBER: 1,
            cls.EDITOR: 2,
            cls.ADMIN: 3,
            cls.OWNER: 4
        }
        return hierarchy.get(role, 0) >= hierarchy.get(required, 0)


class Membership(Base):
    """
    Association between users and tenants with roles.
    
    A user can belong to multiple tenants with different roles.
    """
    __tablename__ = "memberships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(Role), nullable=False, default=Role.MEMBER)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Additional fields
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    invitation_accepted = Column(DateTime, nullable=True)
    is_active = Column(String, default="true", nullable=False)  # Using String for compatibility
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="memberships")
    tenant = relationship("Tenant", back_populates="memberships")
    inviter = relationship("User", foreign_keys=[invited_by])
    
    # Unique constraint - a user can only have one membership per tenant
    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant_membership'),
    )
    
    def __repr__(self):
        return f"<Membership(user_id={self.user_id}, tenant_id={self.tenant_id}, role={self.role})>"
    
    def has_permission(self, required_role: str) -> bool:
        """Check if this membership has the required permission level."""
        return Role.has_permission(self.role, required_role)
    
    def promote(self, new_role: Role):
        """Promote user to a new role."""
        if Role.has_permission(new_role, self.role):
            self.role = new_role
            self.updated_at = datetime.utcnow()
            return True
        return False
    
    def demote(self, new_role: Role):
        """Demote user to a lower role."""
        if not Role.has_permission(new_role, self.role):
            self.role = new_role
            self.updated_at = datetime.utcnow()
            return True
        return False