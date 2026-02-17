"""
Admin schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.admin import AdminRole


class AdminBase(BaseModel):
    """Base admin schema"""
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    role: AdminRole = AdminRole.POLLING_OFFICER


class AdminCreate(AdminBase):
    """Schema for creating a new admin"""
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password meets minimum requirements"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class AdminUpdate(BaseModel):
    """Schema for updating an admin"""
    email: Optional[EmailStr] = None
    role: Optional[AdminRole] = None
    is_active: Optional[bool] = None
    mfa_enabled: Optional[bool] = None


class AdminResponse(AdminBase):
    """Schema for admin response"""
    id: UUID
    mfa_enabled: bool
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
