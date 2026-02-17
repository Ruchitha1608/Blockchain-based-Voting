"""
Voter schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class VoterBase(BaseModel):
    """Base voter schema"""
    voter_id: str = Field(..., min_length=1, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=300)
    address: Optional[str] = None
    age: int = Field(..., ge=18, le=120)


class VoterCreate(VoterBase):
    """Schema for creating a voter (includes biometric data)"""
    constituency_id: UUID
    face_image: str = Field(..., description="Base64 encoded face image")
    fingerprint_image: Optional[str] = Field(None, description="Base64 encoded fingerprint image (optional)")


class VoterResponse(VoterBase):
    """Schema for voter response (excludes biometric data)"""
    id: UUID
    constituency_id: UUID
    blockchain_voter_id: str
    has_voted: bool
    voted_at: Optional[datetime]
    locked_out: bool
    registered_at: datetime

    class Config:
        from_attributes = True


class AuthAttemptResponse(BaseModel):
    """Schema for authentication attempt response"""
    id: UUID
    voter_id: Optional[UUID]
    session_id: Optional[UUID]
    auth_method: str
    outcome: str
    failure_reason: Optional[str]
    similarity_score: Optional[Decimal]
    attempted_at: datetime

    class Config:
        from_attributes = True


class VoteSubmissionResponse(BaseModel):
    """Schema for vote submission response"""
    id: UUID
    voter_id: UUID
    election_id: UUID
    tx_hash: str
    block_number: int
    submitted_at: datetime

    class Config:
        from_attributes = True


class BiometricAuthRequest(BaseModel):
    """Schema for biometric authentication request"""
    face_image: Optional[str] = Field(None, description="Base64 encoded face image")
    fingerprint_image: Optional[str] = Field(None, description="Base64 encoded fingerprint image")
    session_id: UUID


class BiometricAuthResponse(BaseModel):
    """Schema for biometric authentication response"""
    success: bool
    voter_id: Optional[str] = None
    voter_name: Optional[str] = None
    constituency_id: Optional[UUID] = None
    auth_token: Optional[str] = None
    needs_fingerprint: bool = False
    message: str


class VoteCastRequest(BaseModel):
    """Schema for vote casting request"""
    candidate_id: int = Field(..., ge=1)
    confirmed: bool = Field(..., description="User must confirm their choice")


class VoteCastResponse(BaseModel):
    """Schema for vote cast response"""
    success: bool
    tx_hash: str
    block_number: int
    message: str
