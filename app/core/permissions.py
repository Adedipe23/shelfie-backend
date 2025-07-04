from enum import Enum
from typing import Dict, List, Set

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User, UserRole


class PermissionType(str, Enum):
    """Permission type enumeration."""

    # User management
    CREATE_USER = "users:create"
    READ_USER = "users:read"
    UPDATE_USER = "users:update"
    DELETE_USER = "users:delete"

    # Inventory management
    CREATE_PRODUCT = "inventory:create"
    READ_PRODUCT = "inventory:read"
    UPDATE_PRODUCT = "inventory:update"
    DELETE_PRODUCT = "inventory:delete"
    MANAGE_STOCK = "inventory:manage_stock"

    # Supplier management
    CREATE_SUPPLIER = "inventory:create_supplier"
    READ_SUPPLIER = "inventory:read_supplier"
    UPDATE_SUPPLIER = "inventory:update_supplier"
    DELETE_SUPPLIER = "inventory:delete_supplier"

    # Sales management
    CREATE_ORDER = "sales:create"
    READ_ORDER = "sales:read"
    UPDATE_ORDER = "sales:update"
    COMPLETE_ORDER = "sales:complete"
    CANCEL_ORDER = "sales:cancel"
    REFUND_ORDER = "sales:refund"

    # Reporting
    VIEW_REPORTS = "reports:view"
    EXPORT_REPORTS = "reports:export"


class PermissionRegistry:
    """Registry for managing role-based permissions."""

    # Standard role permissions
    _standard_permissions: Dict[UserRole, Set[str]] = {
        UserRole.ADMIN: set(),  # Admins have all permissions by default
        UserRole.MANAGER: set(),
        UserRole.CASHIER: set(),
    }

    # Custom role permissions
    _custom_permissions: Dict[str, Set[str]] = {}

    # All available permissions
    _all_permissions: Set[str] = set()

    @classmethod
    def register_permission(cls, permission: str, roles: List[UserRole] = None) -> None:
        """
        Register a permission and assign it to roles.

        Args:
            permission: Permission name
            roles: Roles to assign the permission to (None means admin only)
        """
        # Add to all permissions
        cls._all_permissions.add(permission)

        # Always give admins all permissions
        cls._standard_permissions[UserRole.ADMIN].add(permission)

        # Assign to other roles if specified
        if roles:
            for role in roles:
                if role != UserRole.ADMIN:  # Admin already has all permissions
                    cls._standard_permissions[role].add(permission)

    @classmethod
    def register_custom_role(cls, role_name: str, permissions: Set[str]) -> None:
        """
        Register a custom role with specific permissions.

        Args:
            role_name: Name of the custom role
            permissions: Set of permissions for the role
        """
        # Validate permissions
        for permission in permissions:
            if permission not in cls._all_permissions:
                raise ValueError(f"Unknown permission: {permission}")

        cls._custom_permissions[role_name] = permissions

    @classmethod
    def get_role_permissions(cls, role: str) -> Set[str]:
        """
        Get the permissions for a role.

        Args:
            role: Role to get permissions for

        Returns:
            Set of permissions for the role
        """
        # Check if it's a standard role
        try:
            standard_role = UserRole(role)
            return cls._standard_permissions.get(standard_role, set())
        except ValueError:
            # It's a custom role
            return cls._custom_permissions.get(role, set())

    @classmethod
    def has_permission(cls, user: User, permission: str) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user: User to check
            permission: Permission to check for

        Returns:
            True if the user has the permission, False otherwise
        """
        # Superusers have all permissions
        if user.is_superuser:
            return True

        # Get permissions for the user's role
        role_permissions = cls.get_role_permissions(user.role)

        # Check if the user has the permission
        return permission in role_permissions

    @classmethod
    def get_all_permissions(cls) -> Set[str]:
        """
        Get all registered permissions.

        Returns:
            Set of all permissions
        """
        return cls._all_permissions

    @classmethod
    def get_all_roles(cls) -> Dict[str, Set[str]]:
        """
        Get all roles with their permissions.

        Returns:
            Dictionary of roles and their permissions
        """
        result = {}

        # Add standard roles
        for role in UserRole:
            result[role.value] = cls._standard_permissions.get(role, set())

        # Add custom roles
        for role, permissions in cls._custom_permissions.items():
            result[role] = permissions

        return result


# Define permission dependency
def require_permission(permission: str):
    """
    Dependency for requiring a specific permission.

    Args:
        permission: Required permission

    Returns:
        Dependency function
    """

    async def _require_permission(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """Check if the current user has the required permission."""
        if not PermissionRegistry.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user

    return _require_permission


# Register common permissions
def register_common_permissions():
    """Register common permissions for the application."""
    # User management
    PermissionRegistry.register_permission("users:create", [UserRole.ADMIN])
    PermissionRegistry.register_permission(
        "users:read", [UserRole.ADMIN, UserRole.MANAGER]
    )
    PermissionRegistry.register_permission("users:update", [UserRole.ADMIN])
    PermissionRegistry.register_permission("users:delete", [UserRole.ADMIN])

    # Inventory management
    PermissionRegistry.register_permission(
        "inventory:create", [UserRole.ADMIN, UserRole.MANAGER]
    )
    PermissionRegistry.register_permission(
        "inventory:read", [UserRole.ADMIN, UserRole.MANAGER, UserRole.CASHIER]
    )
    PermissionRegistry.register_permission(
        "inventory:update", [UserRole.ADMIN, UserRole.MANAGER]
    )
    PermissionRegistry.register_permission(
        "inventory:delete", [UserRole.ADMIN, UserRole.MANAGER]
    )
    PermissionRegistry.register_permission(
        "inventory:manage_stock", [UserRole.ADMIN, UserRole.MANAGER]
    )

    # Sales management
    PermissionRegistry.register_permission(
        "sales:create", [UserRole.ADMIN, UserRole.MANAGER, UserRole.CASHIER]
    )
    PermissionRegistry.register_permission(
        "sales:read", [UserRole.ADMIN, UserRole.MANAGER, UserRole.CASHIER]
    )
    PermissionRegistry.register_permission(
        "sales:update", [UserRole.ADMIN, UserRole.MANAGER]
    )
    PermissionRegistry.register_permission(
        "sales:complete", [UserRole.ADMIN, UserRole.MANAGER, UserRole.CASHIER]
    )
    PermissionRegistry.register_permission(
        "sales:cancel", [UserRole.ADMIN, UserRole.MANAGER, UserRole.CASHIER]
    )
    PermissionRegistry.register_permission(
        "sales:refund", [UserRole.ADMIN, UserRole.MANAGER]
    )

    # Reporting
    PermissionRegistry.register_permission(
        "reports:view", [UserRole.ADMIN, UserRole.MANAGER]
    )
    PermissionRegistry.register_permission(
        "reports:export", [UserRole.ADMIN, UserRole.MANAGER]
    )


# Initialize permissions
register_common_permissions()
