from enum import Enum
from typing import ClassVar, Optional, Union

from sqlalchemy import Column, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field

from app.core.password import get_password_hash, verify_password
from app.models.base import BaseModel


class UserRole(str, Enum):
    """User role enumeration for standard roles."""

    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"


class User(BaseModel, table=True):
    """User model for authentication and authorization."""

    __tablename__: ClassVar[str] = "users"

    email: str = Field(
        sa_column=Column(String, unique=True, index=True, nullable=False)
    )
    hashed_password: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    role: str = Field(default=UserRole.CASHIER)  # Can be standard or custom role
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str) -> Optional["User"]:
        """Get a user by email."""
        query = select(cls).where(cls.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db: AsyncSession, *, obj_in: dict) -> "User":
        """Create a new user with password hashing."""
        # Handle role conversion from enum to string if needed
        role = obj_in.get("role", UserRole.CASHIER)
        if isinstance(role, UserRole):
            role = role.value

        db_obj = cls(
            email=obj_in["email"],
            hashed_password=get_password_hash(obj_in["password"]),
            full_name=obj_in["full_name"],
            role=role,
            is_active=obj_in.get("is_active", True),
            is_superuser=obj_in.get("is_superuser", False),
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    def verify_password(self, password: str) -> bool:
        """Verify a password against the user's hashed password."""
        return verify_password(password, self.hashed_password)

    async def update_password(self, db: AsyncSession, new_password: str) -> None:
        """Update the user's password."""
        self.hashed_password = get_password_hash(new_password)
        db.add(self)
        await db.commit()
        await db.refresh(self)

    def has_standard_role(self, role: UserRole) -> bool:
        """Check if the user has a specific standard role."""
        return self.role == role.value

    def has_role(self, role: Union[UserRole, str]) -> bool:
        """Check if the user has a specific role (standard or custom)."""
        if isinstance(role, UserRole):
            return self.role == role.value
        return self.role == role
