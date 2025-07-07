from typing import List, Set

from pydantic import BaseModel, Field


class CustomRoleCreate(BaseModel):
    """Schema for creating a custom role."""

    role_name: str = Field(..., description="Name of the custom role")
    permissions: Set[str] = Field(..., description="Set of permissions for the role")


class CustomRoleUpdate(BaseModel):
    """Schema for updating a custom role."""

    permissions: Set[str] = Field(..., description="Set of permissions for the role")


class RoleResponse(BaseModel):
    """Schema for role response."""

    name: str = Field(..., description="Name of the role")
    permissions: List[str] = Field(..., description="List of permissions for the role")
