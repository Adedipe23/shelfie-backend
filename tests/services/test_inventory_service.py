import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models.inventory import Product, Supplier
from app.models.user import User, UserRole
from app.services.inventory_service import ProductQueryManager, SupplierQueryManager


@pytest.mark.asyncio
async def test_product_query_manager_filter_for_user():
    """Test filtering products based on user permissions."""
    # Create the manager
    manager = ProductQueryManager()

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

    # Create a base query
    query = select(Product)

    # Test filtering for admin (should see all products)
    admin_query = manager.filter_for_user(query, admin)
    assert str(admin_query) == str(query)

    # Test filtering for cashier (should see all products)
    cashier_query = manager.filter_for_user(query, cashier)
    assert str(cashier_query) == str(query)

    # Test filtering for anonymous (should see no products)
    anon_query = manager.filter_for_user(query, None)
    assert str(anon_query) != str(query)


@pytest.mark.asyncio
async def test_product_query_manager_permission_checks():
    """Test product permission checks."""
    # Create the manager
    manager = ProductQueryManager()

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

    # Create a test product
    product = Product(
        id=1, name="Test Product", sku="TEST001", price=10.0, quantity=100
    )

    # Test create permission
    manager.check_create_permission(admin)  # Admin can create products
    manager.check_create_permission(manager_user)  # Manager can create products

    with pytest.raises(HTTPException):
        manager.check_create_permission(cashier)  # Cashier can't create products

    # Test update permission
    manager.check_update_permission(product, admin)  # Admin can update products
    manager.check_update_permission(
        product, manager_user
    )  # Manager can update products

    with pytest.raises(HTTPException):
        manager.check_update_permission(
            product, cashier
        )  # Cashier can't update products

    # Test delete permission
    manager.check_delete_permission(product, admin)  # Admin can delete products
    manager.check_delete_permission(
        product, manager_user
    )  # Manager can delete products

    with pytest.raises(HTTPException):
        manager.check_delete_permission(
            product, cashier
        )  # Cashier can't delete products


@pytest.mark.asyncio
async def test_supplier_query_manager_permission_checks():
    """Test supplier permission checks."""
    # Create the manager
    manager = SupplierQueryManager()

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

    # Create a test supplier
    supplier = Supplier(id=1, name="Test Supplier")

    # Test create permission
    manager.check_create_permission(admin)  # Admin can create suppliers
    manager.check_create_permission(manager_user)  # Manager can create suppliers

    with pytest.raises(HTTPException):
        manager.check_create_permission(cashier)  # Cashier can't create suppliers

    # Test update permission
    manager.check_update_permission(supplier, admin)  # Admin can update suppliers
    manager.check_update_permission(
        supplier, manager_user
    )  # Manager can update suppliers

    with pytest.raises(HTTPException):
        manager.check_update_permission(
            supplier, cashier
        )  # Cashier can't update suppliers

    # Test delete permission
    manager.check_delete_permission(supplier, admin)  # Admin can delete suppliers
    manager.check_delete_permission(
        supplier, manager_user
    )  # Manager can delete suppliers

    with pytest.raises(HTTPException):
        manager.check_delete_permission(
            supplier, cashier
        )  # Cashier can't delete suppliers
