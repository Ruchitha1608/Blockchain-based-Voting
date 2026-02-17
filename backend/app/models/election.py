"""
Election-related models: Election, Constituency, Candidate
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class ElectionStatus(str, enum.Enum):
    """Election status enumeration"""
    DRAFT = "draft"
    CONFIGURED = "configured"
    ACTIVE = "active"
    ENDED = "ended"
    FINALIZED = "finalized"


class Election(Base):
    """
    Election model representing an electoral event
    """
    __tablename__ = "elections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        String(50),
        nullable=False,
        default=ElectionStatus.DRAFT.value,
        index=True
    )

    voting_start_at = Column(DateTime(timezone=True), nullable=True)
    voting_end_at = Column(DateTime(timezone=True), nullable=True)

    # Smart contract addresses
    contract_address = Column(String(42), nullable=True, index=True)
    voting_contract_address = Column(String(42), nullable=True)
    registry_contract_address = Column(String(42), nullable=True)
    tally_contract_address = Column(String(42), nullable=True)

    # Blockchain metadata
    network_id = Column(Integer, nullable=True)
    deployer_address = Column(String(42), nullable=True)

    # Admin tracking
    created_by = Column(UUID(as_uuid=True), ForeignKey("admins.id", ondelete="SET NULL"), nullable=True, index=True)
    finalized_by = Column(UUID(as_uuid=True), ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("Admin", back_populates="created_elections", foreign_keys=[created_by])
    finalizer = relationship("Admin", back_populates="finalized_elections", foreign_keys=[finalized_by])
    constituencies = relationship("Constituency", back_populates="election", cascade="all, delete-orphan")
    candidates = relationship("Candidate", back_populates="election")
    vote_submissions = relationship("VoteSubmission", back_populates="election")
    blockchain_transactions = relationship("BlockchainTransaction", back_populates="election")

    def __repr__(self):
        return f"<Election(id={self.id}, name={self.name}, status={self.status.value})>"


class Constituency(Base):
    """
    Constituency (electoral district) within an election
    """
    __tablename__ = "constituencies"

    __table_args__ = (
        UniqueConstraint("election_id", "code", name="constituencies_unique_per_election"),
        UniqueConstraint("election_id", "on_chain_id", name="constituencies_unique_on_chain_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    on_chain_id = Column(Integer, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    election = relationship("Election", back_populates="constituencies")
    candidates = relationship("Candidate", back_populates="constituency")
    voters = relationship("Voter", back_populates="constituency")

    def __repr__(self):
        return f"<Constituency(id={self.id}, name={self.name}, code={self.code})>"


class Candidate(Base):
    """
    Candidate registered for a constituency in an election
    """
    __tablename__ = "candidates"

    __table_args__ = (
        UniqueConstraint("election_id", "on_chain_id", name="candidates_unique_on_chain_per_election"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id", ondelete="CASCADE"), nullable=False, index=True)
    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(300), nullable=False)
    party = Column(String(200), nullable=True)
    bio = Column(Text, nullable=True)
    on_chain_id = Column(Integer, nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    election = relationship("Election", back_populates="candidates")
    constituency = relationship("Constituency", back_populates="candidates")
    creator = relationship("Admin")

    def __repr__(self):
        return f"<Candidate(id={self.id}, name={self.name}, party={self.party})>"
