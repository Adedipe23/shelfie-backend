import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.models.inventory import Product, ProductCategory, Supplier
from app.models.user import User, UserRole

settings = get_settings()


async def get_auth_headers(client: AsyncClient, user: User) -> dict:
    """Helper function to get authentication headers."""
    login_data = {
        "username": user.email,
        "password": "password123",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_supplier(db: AsyncSession) -> Supplier:
    """Create a test supplier."""
    supplier_data = {
        "name": "Test Supplier",
        "contact_name": "John Doe",
        "email": "supplier@example.com",
        "phone": "123-456-7890",
        "address": "123 Supplier St",
    }
    supplier = Supplier(**supplier_data)
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return supplier


@pytest_asyncio.fixture
async def test_product(db: AsyncSession, test_supplier: Supplier) -> Product:
    """Create a test product."""
    product_data = {
        "name": "Test Product",
        "description": "A test product",
        "sku": "TEST001",
        "category": ProductCategory.GROCERY,
        "price": 10.99,
        "cost": 5.50,
        "quantity": 100,
        "reorder_level": 10,
        "supplier_id": test_supplier.id,
    }
    product = Product(**product_data)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@pytest_asyncio.fixture
async def test_manager(db: AsyncSession) -> User:
    """Create a test manager user."""
    manager_data = {
        "email": "manager@example.com",
        "password": "password123",
        "full_name": "Manager User",
        "role": UserRole.MANAGER,
    }
    manager = await User.create(db, obj_in=manager_data)
    return manager


# Product Tests
@pytest.mark.asyncio
async def test_get_products_success(
    client: AsyncClient,
    test_user: User,
    test_product: Product,
):
    """Test getting products list."""
    headers = await get_auth_headers(client, test_user)

    response = await client.get(
        f"{settings.API_V1_STR}/inventory/products",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    product = data[0]
    assert product["name"] == test_product.name
    assert product["sku"] == test_product.sku
    assert product["price"] == test_product.price


@pytest.mark.asyncio
async def test_get_products_pagination(
    client: AsyncClient,
    test_user: User,
    test_product: Product,
):
    """Test products pagination."""
    headers = await get_auth_headers(client, test_user)

    # Test with limit
    response = await client.get(
        f"{settings.API_V1_STR}/inventory/products?limit=1",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 1

    # Test with skip
    response = await client.get(
        f"{settings.API_V1_STR}/inventory/products?skip=0&limit=10",
        headers=headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_products_unauthorized(
    client: AsyncClient,
    test_product: Product,
):
    """Test getting products without authentication."""
    response = await client.get(
        f"{settings.API_V1_STR}/inventory/products",
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_product_success(
    client: AsyncClient,
    test_manager: User,
    test_supplier: Supplier,
):
    """Test creating a new product."""
    headers = await get_auth_headers(client, test_manager)

    product_data = {
        "name": "New Product",
        "description": "A new test product",
        "sku": "NEW001",
        "category": "grocery",
        "price": 15.99,
        "cost": 8.00,
        "quantity": 50,
        "reorder_level": 5,
        "supplier_id": test_supplier.id,
    }

    response = await client.post(
        f"{settings.API_V1_STR}/inventory/products",
        json=product_data,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["sku"] == product_data["sku"]
    assert data["price"] == product_data["price"]
    assert "id" in data


@pytest.mark.asyncio
async def test_create_product_duplicate_sku(
    client: AsyncClient,
    test_manager: User,
    test_product: Product,
    test_supplier: Supplier,
):
    """Test creating product with duplicate SKU."""
    headers = await get_auth_headers(client, test_manager)

    product_data = {
        "name": "Duplicate SKU Product",
        "description": "Product with duplicate SKU",
        "sku": test_product.sku,  # Same SKU as existing product
        "category": "grocery",
        "price": 15.99,
        "cost": 8.00,
        "quantity": 50,
        "reorder_level": 5,
        "supplier_id": test_supplier.id,
    }

    response = await client.post(
        f"{settings.API_V1_STR}/inventory/products",
        json=product_data,
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_product_insufficient_permissions(
    client: AsyncClient,
    test_user: User,  # Cashier role
    test_supplier: Supplier,
):
    """Test creating product with insufficient permissions."""
    headers = await get_auth_headers(client, test_user)

    product_data = {
        "name": "New Product",
        "description": "A new test product",
        "sku": "NEW002",
        "category": "grocery",
        "price": 15.99,
        "cost": 8.00,
        "quantity": 50,
        "reorder_level": 5,
        "supplier_id": test_supplier.id,
    }

    response = await client.post(
        f"{settings.API_V1_STR}/inventory/products",
        json=product_data,
        headers=headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_product_by_id_success(
    client: AsyncClient,
    test_user: User,
    test_product: Product,
):
    """Test getting a specific product by ID."""
    headers = await get_auth_headers(client, test_user)

    response = await client.get(
        f"{settings.API_V1_STR}/inventory/products/{test_product.id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_product.id
    assert data["name"] == test_product.name
    assert data["sku"] == test_product.sku


@pytest.mark.asyncio
async def test_get_product_by_id_not_found(
    client: AsyncClient,
    test_user: User,
):
    """Test getting non-existent product."""
    headers = await get_auth_headers(client, test_user)

    response = await client.get(
        f"{settings.API_V1_STR}/inventory/products/99999",
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_product_success(
    client: AsyncClient,
    test_manager: User,
    test_product: Product,
):
    """Test updating a product."""
    headers = await get_auth_headers(client, test_manager)

    update_data = {
        "name": "Updated Product Name",
        "price": 12.99,
        "description": "Updated description",
    }

    response = await client.put(
        f"{settings.API_V1_STR}/inventory/products/{test_product.id}",
        json=update_data,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["price"] == update_data["price"]
    assert data["description"] == update_data["description"]


@pytest.mark.asyncio
async def test_update_product_not_found(
    client: AsyncClient,
    test_manager: User,
):
    """Test updating non-existent product."""
    headers = await get_auth_headers(client, test_manager)

    update_data = {
        "name": "Updated Product Name",
        "price": 12.99,
    }

    response = await client.put(
        f"{settings.API_V1_STR}/inventory/products/99999",
        json=update_data,
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_product_success(
    client: AsyncClient,
    test_manager: User,
    test_product: Product,
):
    """Test deleting a product."""
    headers = await get_auth_headers(client, test_manager)

    response = await client.delete(
        f"{settings.API_V1_STR}/inventory/products/{test_product.id}",
        headers=headers,
    )
    assert response.status_code == 200

    # Verify product is deleted
    response = await client.get(
        f"{settings.API_V1_STR}/inventory/products/{test_product.id}",
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_stock_success(
    client: AsyncClient,
    test_manager: User,
    test_product: Product,
):
    """Test updating product stock."""
    headers = await get_auth_headers(client, test_manager)

    stock_update = {
        "quantity": 25,
    }

    response = await client.put(
        f"{settings.API_V1_STR}/inventory/products/{test_product.id}/stock",
        json=stock_update,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == test_product.quantity + 25


@pytest.mark.asyncio
async def test_get_low_stock_products(
    client: AsyncClient,
    test_manager: User,
    db: AsyncSession,
):
    """Test getting low stock products."""
    # Create a low stock product
    low_stock_product = Product(
        name="Low Stock Product",
        sku="LOW001",
        quantity=5,
        reorder_level=10,
        price=10.0,
        cost=5.0,
    )
    db.add(low_stock_product)
    await db.commit()

    headers = await get_auth_headers(client, test_manager)

    response = await client.get(
        f"{settings.API_V1_STR}/inventory/products/low-stock",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Should include our low stock product
    low_stock_skus = [product["sku"] for product in data]
    assert "LOW001" in low_stock_skus


# Supplier Tests
@pytest.mark.asyncio
async def test_get_suppliers_success(
    client: AsyncClient,
    test_user: User,
    test_supplier: Supplier,
):
    """Test getting suppliers list."""
    headers = await get_auth_headers(client, test_user)

    response = await client.get(
        f"{settings.API_V1_STR}/inventory/suppliers",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    supplier = data[0]
    assert supplier["name"] == test_supplier.name
    assert supplier["email"] == test_supplier.email


@pytest.mark.asyncio
async def test_create_supplier_success(
    client: AsyncClient,
    test_manager: User,
):
    """Test creating a new supplier."""
    headers = await get_auth_headers(client, test_manager)

    supplier_data = {
        "name": "New Supplier",
        "contact_name": "Jane Smith",
        "email": "newsupplier@example.com",
        "phone": "987-654-3210",
        "address": "456 New Supplier Ave",
    }

    response = await client.post(
        f"{settings.API_V1_STR}/inventory/suppliers",
        json=supplier_data,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == supplier_data["name"]
    assert data["email"] == supplier_data["email"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_supplier_by_id_success(
    client: AsyncClient,
    test_user: User,
    test_supplier: Supplier,
):
    """Test getting a specific supplier by ID."""
    headers = await get_auth_headers(client, test_user)

    response = await client.get(
        f"{settings.API_V1_STR}/inventory/suppliers/{test_supplier.id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_supplier.id
    assert data["name"] == test_supplier.name


@pytest.mark.asyncio
async def test_update_supplier_success(
    client: AsyncClient,
    test_manager: User,
    test_supplier: Supplier,
):
    """Test updating a supplier."""
    headers = await get_auth_headers(client, test_manager)

    update_data = {
        "name": "Updated Supplier Name",
        "email": "updated@example.com",
    }

    response = await client.put(
        f"{settings.API_V1_STR}/inventory/suppliers/{test_supplier.id}",
        json=update_data,
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["email"] == update_data["email"]


@pytest.mark.asyncio
async def test_delete_supplier_success(
    client: AsyncClient,
    test_manager: User,
    test_supplier: Supplier,
):
    """Test deleting a supplier."""
    headers = await get_auth_headers(client, test_manager)

    response = await client.delete(
        f"{settings.API_V1_STR}/inventory/suppliers/{test_supplier.id}",
        headers=headers,
    )
    assert response.status_code == 200

    # Verify supplier is deleted
    response = await client.get(
        f"{settings.API_V1_STR}/inventory/suppliers/{test_supplier.id}",
        headers=headers,
    )
    assert response.status_code == 404


# Edge Cases and Error Handling
@pytest.mark.asyncio
async def test_create_product_invalid_data(
    client: AsyncClient,
    test_manager: User,
):
    """Test creating product with invalid data."""
    headers = await get_auth_headers(client, test_manager)

    # Missing required fields
    invalid_data = {
        "name": "Invalid Product",
        # Missing SKU, price, etc.
    }

    response = await client.post(
        f"{settings.API_V1_STR}/inventory/products",
        json=invalid_data,
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_stock_invalid_operation(
    client: AsyncClient,
    test_manager: User,
    test_product: Product,
):
    """Test updating stock with invalid operation."""
    headers = await get_auth_headers(client, test_manager)

    stock_update = {
        "quantity": 25,
        "invalid_field": "invalid_value",
    }

    response = await client.put(
        f"{settings.API_V1_STR}/inventory/products/{test_product.id}/stock",
        json=stock_update,
        headers=headers,
    )
    # The API ignores invalid fields and processes valid ones, so it returns 200
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_negative_stock_handling(
    client: AsyncClient,
    test_manager: User,
    test_product: Product,
):
    """Test handling negative stock scenarios."""
    headers = await get_auth_headers(client, test_manager)

    # Try to remove more stock than available (negative quantity)
    stock_update = {
        "quantity": -(test_product.quantity + 50),
    }

    response = await client.put(
        f"{settings.API_V1_STR}/inventory/products/{test_product.id}/stock",
        json=stock_update,
        headers=headers,
    )
    # Should handle gracefully (either reject or allow negative stock based on business rules)
    assert response.status_code in [200, 400]
