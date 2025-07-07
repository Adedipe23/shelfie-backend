import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.services.user_service import UserQueryManager


@pytest.mark.asyncio
async def test_user_query_manager_filter_for_user(db: AsyncSession):
    """Test filtering users based on user permissions."""
    # Create the manager
    manager = UserQueryManager()

    # Create test users
    admin = User(
        id=1,
        email="admin@example.com",
        hashed_password="",
        full_name="Admin",
        role=UserRole.ADMIN.value,
        is_superuser=True,
    )
    manager_user = User(
        id=2,
        email="manager@example.com",
        hashed_password="",
        full_name="Manager",
        role=UserRole.MANAGER.value,
    )
    cashier = User(
        id=3,
        email="cashier@example.com",
        hashed_password="",
        full_name="Cashier",
        role=UserRole.CASHIER.value,
    )

    # Create a base query
    query = select(User)

    # Test filtering for admin (should see all users)
    admin_query = manager.filter_for_user(query, admin)
    assert str(admin_query) == str(query)

    # Test filtering for manager (should see all users)
    manager_query = manager.filter_for_user(query, manager_user)
    assert str(manager_query) == str(query)

    # Test filtering for cashier (should only see themselves)
    cashier_query = manager.filter_for_user(query, cashier)
    assert str(cashier_query) != str(query)
    assert "users.id = :id_1" in str(cashier_query)


@pytest.mark.asyncio
async def test_user_query_manager_permission_checks():
    """Test user permission checks."""
    # Create the manager
    manager = UserQueryManager()

    # Create test users
    admin = User(
        id=1,
        email="admin@example.com",
        hashed_password="",
        full_name="Admin",
        role=UserRole.ADMIN.value,
        is_superuser=True,
    )
    cashier = User(
        id=2,
        email="cashier@example.com",
        hashed_password="",
        full_name="Cashier",
        role=UserRole.CASHIER.value,
    )

    # Test create permission
    manager.check_create_permission(admin)  # Admin can create users
    manager.check_create_permission(
        None
    )  # Anonymous can create users (for registration)

    # Test update permission
    manager.check_update_permission(admin, admin)  # Admin can update themselves
    manager.check_update_permission(cashier, admin)  # Admin can update others
    manager.check_update_permission(cashier, cashier)  # Users can update themselves

    with pytest.raises(HTTPException):
        manager.check_update_permission(admin, cashier)  # Cashier can't update admin

    # Test delete permission
    manager.check_delete_permission(cashier, admin)  # Admin can delete others

    with pytest.raises(HTTPException):
        manager.check_delete_permission(admin, admin)  # Users can't delete themselves

    with pytest.raises(HTTPException):
        manager.check_delete_permission(admin, cashier)  # Cashier can't delete admin
