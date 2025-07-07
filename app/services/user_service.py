from fastapi import HTTPException, status
from sqlalchemy.sql import Select

from app.core.permissions import PermissionRegistry
from app.core.query_manager import QueryManager
from app.models.user import User


class UserQueryManager(QueryManager[User]):
    """Query manager for User model."""

    def __init__(self):
        """Initialize with User model."""
        super().__init__(User)

    def filter_for_user(self, query: Select, user: User = None) -> Select:
        """
        Filter users based on user permissions.
        Users can always see themselves.

        Args:
            query: SQLAlchemy query
            user: User for permission filtering

        Returns:
            Filtered query
        """
        # If no user, return no users
        if not user:
            return query.where(False)

        # If user has read permission, return all users
        if PermissionRegistry.has_permission(user, "users:read"):
            return query

        # Otherwise, return only the user themselves
        return query.where(User.id == user.id)

    def check_create_permission(self, user: User = None) -> None:
        """
        Check if user has permission to create users.

        Args:
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        # Allow user creation without authentication for registration
        if user and not PermissionRegistry.has_permission(user, "users:create"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create users",
            )

    def check_update_permission(self, obj: User, user: User = None) -> None:
        """
        Check if user has permission to update a user.
        Users can always update themselves.

        Args:
            obj: User to update
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authentication required",
            )

        # Users can update themselves
        if obj.id == user.id:
            return

        # Otherwise, check update permission
        if not PermissionRegistry.has_permission(user, "users:update"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update other users",
            )

    def check_delete_permission(self, obj: User, user: User = None) -> None:
        """
        Check if user has permission to delete a user.
        Users cannot delete themselves.

        Args:
            obj: User to delete
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authentication required",
            )

        # Users cannot delete themselves
        if obj.id == user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Users cannot delete themselves",
            )

        # Check delete permission
        if not PermissionRegistry.has_permission(user, "users:delete"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete users",
            )


# Create instance for use in API routes
user_manager = UserQueryManager()
