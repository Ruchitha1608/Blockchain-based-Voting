"""
Pydantic schemas for request/response validation
"""
from app.schemas.admin import (
    AdminBase,
    AdminCreate,
    AdminUpdate,
    AdminResponse,
    AdminRole
)
from app.schemas.election import (
    ElectionBase,
    ElectionCreate,
    ElectionUpdate,
    ElectionResponse,
    ConstituencyBase,
    ConstituencyCreate,
    ConstituencyResponse,
    CandidateBase,
    CandidateCreate,
    CandidateUpdate,
    CandidateResponse,
    ElectionStatus
)
from app.schemas.voter import (
    VoterBase,
    VoterCreate,
    VoterResponse,
    AuthAttemptResponse,
    VoteSubmissionResponse
)
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    MFASetupResponse,
    MFAVerifyRequest
)

__all__ = [
    "AdminBase",
    "AdminCreate",
    "AdminUpdate",
    "AdminResponse",
    "AdminRole",
    "ElectionBase",
    "ElectionCreate",
    "ElectionUpdate",
    "ElectionResponse",
    "ConstituencyBase",
    "ConstituencyCreate",
    "ConstituencyResponse",
    "CandidateBase",
    "CandidateCreate",
    "CandidateUpdate",
    "CandidateResponse",
    "ElectionStatus",
    "VoterBase",
    "VoterCreate",
    "VoterResponse",
    "AuthAttemptResponse",
    "VoteSubmissionResponse",
    "LoginRequest",
    "LoginResponse",
    "TokenRefreshRequest",
    "TokenRefreshResponse",
    "MFASetupResponse",
    "MFAVerifyRequest",
]
