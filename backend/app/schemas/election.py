"""
Election schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.election import ElectionStatus


class ConstituencyBase(BaseModel):
    """Base constituency schema"""
    name: str = Field(..., min_length=2, max_length=200)
    code: str = Field(..., min_length=2, max_length=50)
    on_chain_id: int = Field(..., ge=0)


class ConstituencyCreate(BaseModel):
    """Schema for creating a constituency"""
    name: str = Field(..., min_length=2, max_length=200)
    code: str = Field(..., min_length=2, max_length=50)
    on_chain_id: Optional[int] = Field(None, ge=0)


class ConstituencyResponse(ConstituencyBase):
    """Schema for constituency response"""
    id: UUID
    election_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class CandidateBase(BaseModel):
    """Base candidate schema"""
    name: str = Field(..., min_length=2, max_length=300)
    party: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = None
    on_chain_id: int = Field(..., ge=0)


class CandidateCreate(BaseModel):
    """Schema for creating a candidate"""
    name: str = Field(..., min_length=2, max_length=300)
    party: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = None
    on_chain_id: Optional[int] = Field(None, ge=0)
    constituency_id: UUID


class CandidateUpdate(BaseModel):
    """Schema for updating a candidate"""
    name: Optional[str] = Field(None, min_length=2, max_length=300)
    party: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = None
    is_active: Optional[bool] = None


class CandidateResponse(CandidateBase):
    """Schema for candidate response"""
    id: UUID
    election_id: UUID
    constituency_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ElectionBase(BaseModel):
    """Base election schema"""
    name: str = Field(..., min_length=3, max_length=300)
    description: Optional[str] = None


class ElectionCreate(ElectionBase):
    """Schema for creating an election"""
    voting_start_at: Optional[datetime] = None
    voting_end_at: Optional[datetime] = None


class ElectionUpdate(BaseModel):
    """Schema for updating an election"""
    name: Optional[str] = Field(None, min_length=3, max_length=300)
    description: Optional[str] = None
    status: Optional[ElectionStatus] = None
    voting_start_at: Optional[datetime] = None
    voting_end_at: Optional[datetime] = None


class ElectionResponse(ElectionBase):
    """Schema for election response"""
    id: UUID
    status: ElectionStatus
    voting_start_at: Optional[datetime]
    voting_end_at: Optional[datetime]
    contract_address: Optional[str]
    voting_contract_address: Optional[str]
    registry_contract_address: Optional[str]
    tally_contract_address: Optional[str]
    network_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    constituencies: List[ConstituencyResponse] = []
    candidates: List[CandidateResponse] = []

    class Config:
        from_attributes = True
