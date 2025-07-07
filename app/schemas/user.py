from typing import List, Optional, Set, Union

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.permissions import PermissionType
from app.models.user import UserRole


# Shared properties
class UserBase(BaseModel):
    """Base user schema with shared properties."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    role: Optional[Union[UserRole, str]] = UserRole.CASHIER


# Properties to receive via API on creation
class UserCreate(UserBase):
    """User creation schema."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    """User update schema."""

    password: Optional[str] = Field(None, min_length=8)


# Properties to return via API
class UserResponse(UserBase):
    """User response schema."""

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    role: str
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)


# Properties for login
class UserLogin(BaseModel):
    """User login schema."""

    email: EmailStr
    password: str


# Custom role schemas
class CustomRoleCreate(BaseModel):
    """Custom role creation schema."""

    name: str
    permissions: Set[PermissionType]

    @field_validator("name")
    @classmethod
    def name_must_not_be_standard_role(cls, v):
        """Validate that the name is not a standard role."""
        if v in [role.value for role in UserRole]:
            raise ValueError(f"Role name '{v}' is a standard role and cannot be used")
        return v


class CustomRoleResponse(BaseModel):
    """Custom role response schema."""

    name: str
    permissions: List[PermissionType]
