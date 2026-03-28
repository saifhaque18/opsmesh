"""
Authentication routes — register, login, token refresh.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.opsmesh.core.database import get_db
from src.opsmesh.models.user import User
from src.opsmesh.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from src.opsmesh.services.auth_service import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    decode_token,
    get_user_by_id,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: DB):
    """Register a new user account."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = await create_user(
        db=db,
        email=data.email,
        name=data.name,
        password=data.password,
        role=data.role,
    )

    access_token = create_access_token(
        user_id=str(user.id), email=user.email, role=user.role.value
    )
    refresh_token = create_refresh_token(user_id=str(user.id))

    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: DB):
    """Authenticate and receive tokens."""
    user = await authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Update last login
    user.last_login_at = datetime.now(UTC)
    await db.flush()
    await db.commit()

    access_token = create_access_token(
        user_id=str(user.id), email=user.email, role=user.role.value
    )
    refresh_token = create_refresh_token(user_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(data: RefreshRequest, db: DB):
    """Get new tokens using a refresh token."""
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await get_user_by_id(db, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token(
        user_id=str(user.id), email=user.email, role=user.role.value
    )
    refresh_token = create_refresh_token(user_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )
