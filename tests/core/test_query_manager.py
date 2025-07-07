import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


@pytest.mark.asyncio
async def test_query_manager_get_by_id(db: AsyncSession):
    """Test QueryManager get_by_id method."""
    # Create a test user first
    test_user = User(
        email="test_get_by_id@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        role=UserRole.CASHIER.value,
    )

    db.add(test_user)
    await db.commit()
    await db.refresh(test_user)

    # Create query manager
    manager = QueryManager(User)

    # Test getting user by ID
    result = await manager.get_by_id(db, test_user.id)
    assert result is not None
    assert result.id == test_user.id
    assert result.email == test_user.email

    # Test getting non-existent user
    result = await manager.get_by_id(db, 99999)
    assert result is None


@pytest.mark.asyncio
async def test_query_manager_get_all(db: AsyncSession):
    """Test QueryManager get_all method."""
    # Create test users
    users = []
    for i in range(5):
        user = User(
            email=f"test_get_all_{i}@example.com",
            hashed_password="hashed_password",
            full_name=f"Test User {i}",
            role=UserRole.CASHIER.value,
        )
        users.append(user)
        db.add(user)

    await db.commit()

    # Create query manager
    manager = QueryManager(User)

    # Test getting all users
    result = await manager.get_all(db)
    assert len(result) >= 5  # At least our test users

    # Test pagination
    result = await manager.get_all(db, skip=0, limit=2)
    assert len(result) == 2

    result = await manager.get_all(db, skip=2, limit=2)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_query_manager_create(db: AsyncSession):
    """Test QueryManager create method."""
    manager = QueryManager(User)

    # Test creating a user
    user_data = {
        "email": "test_create@example.com",
        "hashed_password": "hashed_password",
        "full_name": "Test Create User",
        "role": UserRole.CASHIER.value,
    }

    result = await manager.create(db, user_data)
    assert result is not None
    assert result.email == user_data["email"]
    assert result.full_name == user_data["full_name"]
    assert result.id is not None


@pytest.mark.asyncio
async def test_query_manager_update(db: AsyncSession):
    """Test QueryManager update method."""
    # Create a test user first
    test_user = User(
        email="test_update@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        role=UserRole.CASHIER.value,
    )

    db.add(test_user)
    await db.commit()
    await db.refresh(test_user)

    # Create query manager
    manager = QueryManager(User)

    # Test updating the user
    update_data = {
        "full_name": "Updated Test User",
        "role": UserRole.MANAGER.value,
    }

    result = await manager.update(db, test_user, update_data)
    assert result is not None
    assert result.full_name == "Updated Test User"
    assert result.role == UserRole.MANAGER.value
    assert result.email == test_user.email  # Should remain unchanged


@pytest.mark.asyncio
async def test_query_manager_delete(db: AsyncSession):
    """Test QueryManager delete method."""
    # Create a test user first
    test_user = User(
        email="test_delete@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        role=UserRole.CASHIER.value,
    )

    db.add(test_user)
    await db.commit()
    await db.refresh(test_user)
    user_id = test_user.id

    # Create query manager
    manager = QueryManager(User)

    # Test deleting the user
    result = await manager.delete(db, test_user)
    assert result is not None
    assert result.id == user_id

    # Verify user is deleted
    deleted_user = await manager.get_by_id(db, user_id)
    assert deleted_user is None


@pytest.mark.asyncio
async def test_query_manager_with_custom_permissions(db: AsyncSession):
    """Test QueryManager with custom permission implementations."""

    class RestrictiveQueryManager(QueryManager[User]):
        """Query manager with restrictive permissions."""

        def __init__(self):
            super().__init__(User)

        def check_create_permission(self, user=None):
            if not user or user.role != UserRole.ADMIN.value:
                raise HTTPException(
                    status_code=403, detail="Admin required for creation"
                )

        def check_update_permission(self, obj, user=None):
            if not user:
                raise HTTPException(status_code=403, detail="User required")
            if user.role != UserRole.ADMIN.value and obj.id != user.id:
                raise HTTPException(
                    status_code=403, detail="Can only update own record"
                )

        def check_delete_permission(self, obj, user=None):
            if not user or user.role != UserRole.ADMIN.value:
                raise HTTPException(
                    status_code=403, detail="Admin required for deletion"
                )

    manager = RestrictiveQueryManager()

    # Create test users
    admin_user = User(
        email="admin@example.com",
        hashed_password="hashed_password",
        full_name="Admin User",
        role=UserRole.ADMIN.value,
    )

    regular_user = User(
        email="regular@example.com",
        hashed_password="hashed_password",
        full_name="Regular User",
        role=UserRole.CASHIER.value,
    )

    db.add(admin_user)
    db.add(regular_user)
    await db.commit()
    await db.refresh(admin_user)
    await db.refresh(regular_user)

    # Test create permissions
    user_data = {
        "email": "new_user@example.com",
        "hashed_password": "hashed_password",
        "full_name": "New User",
        "role": UserRole.CASHIER.value,
    }

    # Admin should be able to create
    new_user = await manager.create(db, user_data, admin_user)
    assert new_user is not None

    # Regular user should not be able to create
    with pytest.raises(HTTPException, match="Admin required for creation"):
        await manager.create(db, user_data, regular_user)

    # Test update permissions
    update_data = {"full_name": "Updated Name"}

    # Admin should be able to update anyone
    await manager.update(db, regular_user, update_data, admin_user)

    # Regular user should be able to update themselves
    await manager.update(db, regular_user, update_data, regular_user)

    # Regular user should not be able to update others
    with pytest.raises(HTTPException, match="Can only update own record"):
        await manager.update(db, admin_user, update_data, regular_user)

    # Test delete permissions
    # Admin should be able to delete
    await manager.delete(db, new_user, admin_user)

    # Regular user should not be able to delete
    with pytest.raises(HTTPException, match="Admin required for deletion"):
        await manager.delete(db, regular_user, regular_user)
