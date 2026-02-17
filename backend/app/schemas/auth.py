"""
Authentication schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1, max_length=100)
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=6)


class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    admin_id: str
    username: str
    role: str


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    """Schema for token refresh response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MFASetupResponse(BaseModel):
    """Schema for MFA setup response"""
    secret: str
    qr_code_uri: str
    backup_codes: list[str]


class MFAVerifyRequest(BaseModel):
    """Schema for MFA verification request"""
    code: str = Field(..., min_length=6, max_length=6)


class MFAVerifyResponse(BaseModel):
    """Schema for MFA verification response"""
    success: bool
    message: str


class LogoutRequest(BaseModel):
    """Schema for logout request"""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Schema for password change request"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


# Additional schema aliases for router compatibility
Token = LoginResponse  # Alias for backward compatibility
TokenRefresh = TokenRefreshRequest  # Alias
MFASetup = MFASetupResponse  # Alias
MFAVerify = MFAVerifyRequest  # Alias
