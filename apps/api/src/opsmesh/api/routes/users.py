"""
User management routes — admin only.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.opsmesh.api.deps import AdminUser, CurrentUser
from src.opsmesh.core.database import get_db
from src.opsmesh.models.user import User
from src.opsmesh.schemas.auth import UserResponse, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["users"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: CurrentUser):
    """Get the authenticated user's profile."""
    return user


@router.get("", response_model=list[UserResponse])
async def list_users(db: DB, user: AdminUser):
    """List all users (admin only)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    db: DB,
    admin: AdminUser,
):
    """Update a user's role or status (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from deactivating themselves
    if target_user.id == admin.id and data.is_active is False:
        raise HTTPException(
            status_code=400, detail="Cannot deactivate your own account"
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(target_user, field, value)

    await db.flush()
    await db.refresh(target_user)
    await db.commit()
    return target_user


@router.delete("/{user_id}", status_code=204)
async def deactivate_user(user_id: uuid.UUID, db: DB, admin: AdminUser):
    """Deactivate a user (admin only). Soft delete."""
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user.id == admin.id:
        raise HTTPException(
            status_code=400, detail="Cannot deactivate your own account"
        )

    target_user.is_active = False
    await db.flush()
    await db.commit()
