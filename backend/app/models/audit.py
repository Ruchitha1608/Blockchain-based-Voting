"""
Audit-related models: AuditLog, BlockchainTransaction
"""
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class LogAction(str, enum.Enum):
    """Log action enumeration"""
    ADMIN_CREATED = "admin_created"
    ADMIN_UPDATED = "admin_updated"
    ADMIN_DELETED = "admin_deleted"
    ADMIN_LOGIN = "admin_login"
    ADMIN_LOGOUT = "admin_logout"
    ELECTION_CREATED = "election_created"
    ELECTION_UPDATED = "election_updated"
    ELECTION_STARTED = "election_started"
    ELECTION_CLOSED = "election_closed"
    ELECTION_FINALIZED = "election_finalized"
    VOTER_REGISTERED = "voter_registered"
    VOTER_UPDATED = "voter_updated"
    CANDIDATE_ADDED = "candidate_added"
    CANDIDATE_UPDATED = "candidate_updated"
    CONTRACT_DEPLOYED = "contract_deployed"
    SETTINGS_CHANGED = "settings_changed"


class TxType(str, enum.Enum):
    """Transaction type enumeration"""
    DEPLOY_CONTROLLER = "deploy_controller"
    DEPLOY_REGISTRY = "deploy_registry"
    DEPLOY_BOOTH = "deploy_booth"
    DEPLOY_TALLIER = "deploy_tallier"
    REGISTER_VOTER = "register_voter"
    REGISTER_CANDIDATE = "register_candidate"
    OPEN_VOTING = "open_voting"
    CAST_VOTE = "cast_vote"
    CLOSE_VOTING = "close_voting"
    TALLY_RESULTS = "tally_results"
    FINALIZE_ELECTION = "finalize_election"


class AuditLog(Base):
    """
    Audit log for administrative actions (append-only)
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("admins.id", ondelete="SET NULL"), nullable=True, index=True)

    action = Column(
        String(50),
        nullable=False,
        index=True
    )
    target_table = Column(String(100), nullable=True)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSONB, nullable=True)

    ip_address = Column(INET, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Relationships
    admin = relationship("Admin", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action.value}, admin_id={self.admin_id})>"


class BlockchainTransaction(Base):
    """
    Blockchain transaction log
    """
    __tablename__ = "blockchain_txns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id", ondelete="SET NULL"), nullable=True, index=True)

    tx_type = Column(
        String(50),
        nullable=False,
        index=True
    )
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    block_number = Column(BigInteger, nullable=True)

    from_address = Column(String(42), nullable=False, index=True)
    to_address = Column(String(42), nullable=True)

    gas_used = Column(BigInteger, nullable=True)
    status = Column(Boolean, nullable=False, default=True)
    raw_event = Column(JSONB, nullable=True)

    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Relationships
    election = relationship("Election", back_populates="blockchain_transactions")

    def __repr__(self):
        return f"<BlockchainTransaction(id={self.id}, tx_type={self.tx_type.value}, tx_hash={self.tx_hash})>"
