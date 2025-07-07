from typing import Dict, List, Set

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import PermissionRegistry
from app.models.user import UserRole


class RoleService:
    """Service for managing roles and permissions."""

    @staticmethod
    async def get_all_permissions() -> List[str]:
        """
        Get all available permissions.

        Returns:
            List of all permissions
        """
        return sorted(list(PermissionRegistry.get_all_permissions()))

    @staticmethod
    async def get_all_roles() -> Dict[str, List[str]]:
        """
        Get all roles with their permissions.

        Returns:
            Dictionary of roles and their permissions
        """
        roles = PermissionRegistry.get_all_roles()
        return {role: sorted(list(permissions)) for role, permissions in roles.items()}

    @staticmethod
    async def get_role_permissions(role: str) -> List[str]:
        """
        Get permissions for a specific role.

        Args:
            role: Role to get permissions for

        Returns:
            List of permissions for the role

        Raises:
            HTTPException: If role doesn't exist
        """
        permissions = PermissionRegistry.get_role_permissions(role)
        if not permissions and role not in [r.value for r in UserRole]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role}' not found",
            )
        return sorted(list(permissions))

    @staticmethod
    async def create_custom_role(
        role_name: str, permissions: Set[str]
    ) -> Dict[str, List[str]]:
        """
        Create a new custom role.

        Args:
            role_name: Name of the custom role
            permissions: Set of permissions for the role

        Returns:
            Dictionary with role name and permissions

        Raises:
            HTTPException: If role already exists or permissions are invalid
        """
        # Check if role already exists
        roles = PermissionRegistry.get_all_roles()
        if role_name in roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{role_name}' already exists",
            )

        # Check if role name is a standard role
        if role_name in [r.value for r in UserRole]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role name '{role_name}' is a standard role and cannot be used",
            )

        try:
            PermissionRegistry.register_custom_role(role_name, permissions)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        return {
            "name": role_name,
            "permissions": sorted(list(permissions)),
        }

    @staticmethod
    async def update_custom_role(
        role_name: str, permissions: Set[str]
    ) -> Dict[str, List[str]]:
        """
        Update a custom role's permissions.

        Args:
            role_name: Name of the custom role
            permissions: Set of permissions for the role

        Returns:
            Dictionary with role name and permissions

        Raises:
            HTTPException: If role doesn't exist or permissions are invalid
        """
        # Check if role exists and is a custom role
        if role_name in [r.value for r in UserRole]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update standard role '{role_name}'",
            )

        roles = PermissionRegistry.get_all_roles()
        if role_name not in roles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found",
            )

        try:
            PermissionRegistry.register_custom_role(role_name, permissions)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        return {
            "name": role_name,
            "permissions": sorted(list(permissions)),
        }

    @staticmethod
    async def delete_custom_role(
        role_name: str, db: AsyncSession
    ) -> Dict[str, List[str]]:
        """
        Delete a custom role.

        Args:
            role_name: Name of the custom role
            db: Database session

        Returns:
            Dictionary with role name and permissions

        Raises:
            HTTPException: If role doesn't exist or is in use
        """
        # Check if role exists and is a custom role
        if role_name in [r.value for r in UserRole]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete standard role '{role_name}'",
            )

        roles = PermissionRegistry.get_all_roles()
        if role_name not in roles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found",
            )

        # Check if any users have this role
        from sqlalchemy import text

        query = text("SELECT COUNT(*) FROM users WHERE role = :role")
        result = await db.execute(query, {"role": role_name})
        count = result.scalar()

        if count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete role '{role_name}' because it is assigned to {count} users",
            )

        # Get permissions before deleting
        permissions = list(PermissionRegistry.get_role_permissions(role_name))

        # Delete the role
        PermissionRegistry._custom_permissions.pop(role_name, None)

        return {
            "name": role_name,
            "permissions": sorted(permissions),
        }


# Create instance for use in API routes
role_service = RoleService()
