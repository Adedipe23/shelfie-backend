import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.sales import Order, OrderStatus
from app.models.user import User, UserRole
from app.services.sales_service import OrderQueryManager


@pytest.mark.asyncio
async def test_order_query_manager_filter_for_user():
    """Test filtering orders based on user permissions."""
    # Create the manager
    manager = OrderQueryManager()

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
    cashier1 = User(
        id=3,
        email="cashier1@example.com",
        hashed_password="",
        full_name="Cashier 1",
        role=UserRole.CASHIER.value,
    )
    cashier2 = User(
        id=4,
        email="cashier2@example.com",
        hashed_password="",
        full_name="Cashier 2",
        role=UserRole.CASHIER.value,
    )

    # Create a base query
    query = select(Order)

    # Test filtering for admin (should see all orders)
    admin_query = manager.filter_for_user(query, admin)
    assert str(admin_query) == str(query)

    # Test filtering for manager (should see all orders)
    manager_query = manager.filter_for_user(query, manager_user)
    assert str(manager_query) == str(query)

    # Test filtering for cashier (should only see their own orders)
    cashier1_query = manager.filter_for_user(query, cashier1)
    assert str(cashier1_query) != str(query)
    assert "orders.cashier_id = :cashier_id_1" in str(cashier1_query)

    # Test filtering for anonymous (should see no orders)
    anon_query = manager.filter_for_user(query, None)
    assert str(anon_query) != str(query)


@pytest.mark.asyncio
async def test_order_query_manager_permission_checks():
    """Test order permission checks."""
    # Create the manager
    manager = OrderQueryManager()

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
    cashier1 = User(
        id=3,
        email="cashier1@example.com",
        hashed_password="",
        full_name="Cashier 1",
        role=UserRole.CASHIER.value,
    )
    cashier2 = User(
        id=4,
        email="cashier2@example.com",
        hashed_password="",
        full_name="Cashier 2",
        role=UserRole.CASHIER.value,
    )

    # Create test orders
    order1 = Order(id=1, cashier_id=cashier1.id, status=OrderStatus.PENDING)
    order2 = Order(id=2, cashier_id=cashier2.id, status=OrderStatus.PENDING)

    # Test create permission
    manager.check_create_permission(admin)  # Admin can create orders
    manager.check_create_permission(manager_user)  # Manager can create orders
    manager.check_create_permission(cashier1)  # Cashier can create orders

    with pytest.raises(HTTPException):
        manager.check_create_permission(None)  # Anonymous can't create orders

    # Test update permission
    manager.check_update_permission(order1, admin)  # Admin can update any order
    manager.check_update_permission(
        order1, manager_user
    )  # Manager can update any order
    manager.check_update_permission(
        order1, cashier1
    )  # Cashier can update their own orders

    with pytest.raises(HTTPException):
        manager.check_update_permission(
            order1, cashier2
        )  # Cashier can't update others' orders

    # Test delete permission (orders should not be deleted)
    with pytest.raises(HTTPException):
        manager.check_delete_permission(order1, admin)

    with pytest.raises(HTTPException):
        manager.check_delete_permission(order1, cashier1)
