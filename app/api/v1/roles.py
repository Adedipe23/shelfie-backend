from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.schemas.role import CustomRoleCreate, CustomRoleUpdate, RoleResponse
from app.services import role_service

router = APIRouter()


@router.get("", response_model=Dict[str, List[str]])
@router.get("/", response_model=Dict[str, List[str]])
async def get_all_roles(
    current_user: User = Depends(require_permission("users:read")),
) -> Any:
    """
    Get all roles with their permissions.
    """
    return await role_service.get_all_roles()


@router.get("/permissions", response_model=List[str])
async def get_all_permissions(
    current_user: User = Depends(require_permission("users:read")),
) -> Any:
    """
    Get all available permissions.
    """
    return await role_service.get_all_permissions()


@router.get("/{role_name}/permissions", response_model=List[str])
async def get_role_permissions(
    role_name: str,
    current_user: User = Depends(require_permission("users:read")),
) -> Any:
    """
    Get permissions for a specific role.
    """
    return await role_service.get_role_permissions(role_name)


@router.post("/custom", response_model=RoleResponse)
async def create_custom_role(
    *,
    role_data: CustomRoleCreate,
    current_user: User = Depends(require_permission("users:create")),
) -> Any:
    """
    Create a new custom role.
    """
    return await role_service.create_custom_role(
        role_data.role_name, role_data.permissions
    )


@router.put("/custom/{role_name}", response_model=RoleResponse)
async def update_custom_role(
    *,
    role_name: str,
    role_data: CustomRoleUpdate,
    current_user: User = Depends(require_permission("users:update")),
) -> Any:
    """
    Update a custom role's permissions.
    """
    return await role_service.update_custom_role(role_name, role_data.permissions)


@router.delete("/custom/{role_name}", response_model=RoleResponse)
async def delete_custom_role(
    *,
    role_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("users:delete")),
) -> Any:
    """
    Delete a custom role.
    """
    return await role_service.delete_custom_role(role_name, db)
