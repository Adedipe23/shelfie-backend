import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.core.query_manager import QueryManager
from app.models.user import User, UserRole


class TestQueryManager:
    """Test the QueryManager class."""

    def test_filter_for_user(self):
        """Test filtering queries based on user permissions."""
        # Create a test query manager
        manager = QueryManager(User)

        # Create a test query
        query = select(User)

        # Create a test user
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="",
            full_name="Test User",
            role=UserRole.ADMIN.value,
        )

        # Test filtering
        filtered_query = manager.filter_for_user(query, user)

        # By default, no filtering should be applied
        assert str(filtered_query) == str(query)

    def test_check_permissions(self):
        """Test permission checking methods."""
        # Create a test query manager
        manager = QueryManager(User)

        # Create a test user
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="",
            full_name="Test User",
            role=UserRole.ADMIN.value,
        )

        # Test permission checks (should not raise exceptions by default)
        manager.check_create_permission(user)
        manager.check_update_permission(user, user)
        manager.check_delete_permission(user, user)


@pytest.mark.asyncio
async def test_custom_query_manager():
    """Test a custom query manager with permission checks."""

    class CustomQueryManager(QueryManager[User]):
        """Custom query manager for testing."""

        def __init__(self):
            """Initialize with User model."""
            super().__init__(User)

        def check_create_permission(self, user=None):
            """Check create permission."""
            if not user or user.role != UserRole.ADMIN.value:
                raise HTTPException(status_code=403, detail="Not allowed")

        def check_update_permission(self, obj, user=None):
            """Check update permission."""
            if not user or (user.role != UserRole.ADMIN.value and obj.id != user.id):
                raise HTTPException(status_code=403, detail="Not allowed")

    # Create the custom manager
    manager = CustomQueryManager()

    # Create test users
    admin_user = User(
        id=1,
        email="admin@example.com",
        hashed_password="",
        full_name="Admin",
        role=UserRole.ADMIN.value,
    )
    regular_user = User(
        id=2,
        email="user@example.com",
        hashed_password="",
        full_name="User",
        role=UserRole.CASHIER.value,
    )
    other_user = User(
        id=3,
        email="other@example.com",
        hashed_password="",
        full_name="Other",
        role=UserRole.CASHIER.value,
    )

    # Test create permission
    manager.check_create_permission(admin_user)  # Should not raise exception

    with pytest.raises(HTTPException):
        manager.check_create_permission(regular_user)

    # Test update permission
    manager.check_update_permission(regular_user, admin_user)  # Admin can update anyone
    manager.check_update_permission(
        regular_user, regular_user
    )  # User can update themselves

    with pytest.raises(HTTPException):
        manager.check_update_permission(
            regular_user, other_user
        )  # Other user can't update
