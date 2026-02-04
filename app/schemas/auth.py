"""Auth schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class AuthVerifyRequest(BaseModel):
    """Request to verify Firebase ID token."""

    id_token: str


class UserResponse(BaseModel):
    """User response schema."""

    id: UUID
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    display_name: Optional[str] = None
    is_admin: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthVerifyResponse(BaseModel):
    """Response after successful token verification."""

    user: UserResponse
    message: str = "Authentication successful"
