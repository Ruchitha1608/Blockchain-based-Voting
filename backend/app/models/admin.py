"""
Admin model for system administrators
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class AdminRole(str, enum.Enum):
    """Admin role enumeration"""
    SUPER_ADMIN = "super_admin"
    ELECTION_ADMINISTRATOR = "election_administrator"
    POLLING_OFFICER = "polling_officer"
    AUDITOR = "auditor"


class Admin(Base):
    """
    Admin user model for system access control
    """
    __tablename__ = "admins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(512), nullable=False)
    role = Column(
        String(50),
        nullable=False,
        default=AdminRole.POLLING_OFFICER.value,
        index=True
    )
    mfa_secret = Column(String(255), nullable=True)
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Self-referential foreign key for created_by
    created_by = Column(UUID(as_uuid=True), ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("Admin", remote_side=[id], foreign_keys=[created_by])
    created_elections = relationship("Election", back_populates="creator", foreign_keys="Election.created_by")
    finalized_elections = relationship("Election", back_populates="finalizer", foreign_keys="Election.finalized_by")
    registered_voters = relationship("Voter", back_populates="registrar")
    audit_logs = relationship("AuditLog", back_populates="admin")

    def __repr__(self):
        return f"<Admin(id={self.id}, username={self.username}, role={self.role.value})>"

    def has_permission(self, required_role: AdminRole) -> bool:
        """
        Check if admin has required permission level
        Permission hierarchy: super_admin > election_administrator > polling_officer > auditor
        """
        role_hierarchy = {
            AdminRole.SUPER_ADMIN: 4,
            AdminRole.ELECTION_ADMINISTRATOR: 3,
            AdminRole.POLLING_OFFICER: 2,
            AdminRole.AUDITOR: 1
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)
