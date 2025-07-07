from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_permission
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services import user_manager

router = APIRouter()


@router.get("", response_model=List[UserResponse])
@router.get("/", response_model=List[UserResponse])
async def read_users(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_permission("users:read")),
) -> Any:
    """
    Retrieve users.
    """
    users = await user_manager.get_all(db, skip=skip, limit=limit, user=current_user)
    return users


@router.post("", response_model=UserResponse)
@router.post("/", response_model=UserResponse)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(require_permission("users:create")),
) -> Any:
    """
    Create new user.
    """
    # Check if email already exists
    existing_user = await User.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    # Create user (use User.create directly to ensure password hashing)
    user = await User.create(db, obj_in=user_in.model_dump())
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a specific user by id.
    """
    user = await user_manager.get_by_id(db, user_id, user=current_user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a user.
    """
    # Get user
    user = await user_manager.get_by_id(db, user_id, user=current_user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Handle password separately
    user_data = user_in.model_dump(exclude_unset=True)
    if "password" in user_data and user_data["password"]:
        await user.update_password(db, user_data.pop("password"))

    # Update other fields
    if user_data:
        user = await user_manager.update(db, user, user_data, user=current_user)

    return user


@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    current_user: User = Depends(require_permission("users:delete")),
) -> Any:
    """
    Delete a user.
    """
    # Get user
    user = await user_manager.get_by_id(db, user_id, user=current_user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Delete user
    return await user_manager.delete(db, user, user=current_user)
