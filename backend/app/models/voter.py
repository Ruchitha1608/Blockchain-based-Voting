"""
Voter-related models: Voter, AuthAttempt, VoteSubmission
"""
from sqlalchemy import Column, String, Text, SmallInteger, BigInteger, Boolean, DateTime, Enum as SQLEnum, ForeignKey, DECIMAL, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class AuthMethod(str, enum.Enum):
    """Authentication method enumeration"""
    FACE = "face"
    FINGERPRINT = "fingerprint"


class AuthOutcome(str, enum.Enum):
    """Authentication outcome enumeration"""
    SUCCESS = "success"
    FAILURE = "failure"
    LOCKOUT = "lockout"


class Voter(Base):
    """
    Voter model with biometric data
    """
    __tablename__ = "voters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voter_id = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(300), nullable=False)
    address = Column(Text, nullable=True)
    age = Column(SmallInteger, nullable=False)

    constituency_id = Column(
        UUID(as_uuid=True),
        ForeignKey("constituencies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    # Biometric hashes (SHA-256)
    face_embedding_hash = Column(String(512), nullable=False, index=True)
    fingerprint_template_hash = Column(String(512), nullable=False, index=True)
    biometric_salt = Column(String(64), nullable=False)

    # Encrypted biometric data for similarity comparison
    encrypted_face_embedding = Column(Text, nullable=False)
    encrypted_fingerprint_template = Column(Text, nullable=False)

    # Blockchain identity
    blockchain_voter_id = Column(String(66), unique=True, nullable=False, index=True)

    # Voting status
    has_voted = Column(Boolean, nullable=False, default=False, index=True)
    voted_at = Column(DateTime(timezone=True), nullable=True)
    vote_tx_hash = Column(String(66), nullable=True)

    # Security tracking
    failed_auth_count = Column(SmallInteger, nullable=False, default=0)
    locked_out = Column(Boolean, nullable=False, default=False, index=True)
    lockout_at = Column(DateTime(timezone=True), nullable=True)

    # Registration tracking
    registered_by = Column(UUID(as_uuid=True), ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    registered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    constituency = relationship("Constituency", back_populates="voters")
    registrar = relationship("Admin", back_populates="registered_voters")
    auth_attempts = relationship("AuthAttempt", back_populates="voter")
    vote_submissions = relationship("VoteSubmission", back_populates="voter")

    def __repr__(self):
        return f"<Voter(id={self.id}, voter_id={self.voter_id}, has_voted={self.has_voted})>"


class AuthAttempt(Base):
    """
    Authentication attempt log (append-only)
    """
    __tablename__ = "auth_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voter_id = Column(UUID(as_uuid=True), ForeignKey("voters.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    polling_station = Column(String(200), nullable=True)

    auth_method = Column(
        SQLEnum(AuthMethod, name="auth_method", create_type=False),
        nullable=False,
        index=True
    )
    outcome = Column(
        SQLEnum(AuthOutcome, name="auth_outcome", create_type=False),
        nullable=False,
        index=True
    )
    failure_reason = Column(String(500), nullable=True)
    similarity_score = Column(DECIMAL(5, 4), nullable=True)

    ip_address = Column(INET, nullable=True)
    attempted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Relationships
    voter = relationship("Voter", back_populates="auth_attempts")

    def __repr__(self):
        return f"<AuthAttempt(id={self.id}, method={self.auth_method.value}, outcome={self.outcome.value})>"


class VoteSubmission(Base):
    """
    Vote submission log (append-only)
    """
    __tablename__ = "vote_submissions"

    __table_args__ = (
        UniqueConstraint("voter_id", "election_id", name="vote_submissions_unique_voter_election"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("voters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    election_id = Column(
        UUID(as_uuid=True),
        ForeignKey("elections.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    block_number = Column(BigInteger, nullable=False)
    gas_used = Column(BigInteger, nullable=True)

    submitted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Relationships
    voter = relationship("Voter", back_populates="vote_submissions")
    election = relationship("Election", back_populates="vote_submissions")

    def __repr__(self):
        return f"<VoteSubmission(id={self.id}, voter_id={self.voter_id}, tx_hash={self.tx_hash})>"
