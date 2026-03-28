"""
Authentication schemas for request/response validation.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from src.opsmesh.models.user import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.VIEWER


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: UserRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    role: UserRole | None = None
    is_active: bool | None = None
