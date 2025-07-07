import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import (
    MovementType,
    Product,
    ProductCategory,
    StockMovement,
    Supplier,
)


@pytest_asyncio.fixture
async def test_supplier(db: AsyncSession) -> Supplier:
    """Create a test supplier."""
    supplier = Supplier(
        name="Test Supplier",
        contact_name="John Doe",
        email="supplier@example.com",
        phone="123-456-7890",
        address="123 Supplier St",
    )
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return supplier


@pytest.mark.asyncio
async def test_product_creation(db: AsyncSession, test_supplier: Supplier):
    """Test creating a product."""
    product = Product(
        name="Test Product",
        description="A test product",
        sku="TEST001",
        category=ProductCategory.GROCERY,
        price=10.99,
        cost=5.50,
        quantity=100,
        reorder_level=10,
        supplier_id=test_supplier.id,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    assert product.id is not None
    assert product.name == "Test Product"
    assert product.sku == "TEST001"
    assert product.category == ProductCategory.GROCERY
    assert product.price == 10.99
    assert product.cost == 5.50
    assert product.quantity == 100
    assert product.reorder_level == 10
    assert product.supplier_id == test_supplier.id


@pytest.mark.asyncio
async def test_product_creation_with_defaults(db: AsyncSession):
    """Test creating a product with default values."""
    product = Product(
        name="Default Product",
        sku="DEFAULT001",
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    assert product.description == ""
    assert product.category == ProductCategory.OTHER
    assert product.price == 0.0
    assert product.cost == 0.0
    assert product.quantity == 0
    assert product.reorder_level == 10
    assert product.supplier_id is None


@pytest.mark.asyncio
async def test_get_product_by_sku(db: AsyncSession):
    """Test getting a product by SKU."""
    product = Product(
        name="SKU Test Product",
        sku="SKUTEST001",
        price=15.99,
    )

    db.add(product)
    await db.commit()

    # Find the product
    found_product = await Product.get_by_sku(db, sku="SKUTEST001")

    assert found_product is not None
    assert found_product.name == "SKU Test Product"
    assert found_product.sku == "SKUTEST001"


@pytest.mark.asyncio
async def test_get_product_by_sku_not_found(db: AsyncSession):
    """Test getting a non-existent product by SKU."""
    product = await Product.get_by_sku(db, sku="NONEXISTENT")
    assert product is None


@pytest.mark.asyncio
async def test_get_low_stock_products(db: AsyncSession):
    """Test getting products with low stock."""
    # Create products with different stock levels
    low_stock_product = Product(
        name="Low Stock Product",
        sku="LOW001",
        quantity=5,
        reorder_level=10,
        price=10.0,
    )

    normal_stock_product = Product(
        name="Normal Stock Product",
        sku="NORMAL001",
        quantity=50,
        reorder_level=10,
        price=15.0,
    )

    db.add(low_stock_product)
    db.add(normal_stock_product)
    await db.commit()

    # Get low stock products
    low_stock_products = await Product.get_low_stock_products(db)

    assert len(low_stock_products) >= 1
    low_stock_skus = [p.sku for p in low_stock_products]
    assert "LOW001" in low_stock_skus
    assert "NORMAL001" not in low_stock_skus


@pytest.mark.asyncio
async def test_get_low_stock_products_pagination(db: AsyncSession):
    """Test pagination for low stock products."""
    # Create multiple low stock products
    for i in range(5):
        product = Product(
            name=f"Low Stock Product {i}",
            sku=f"LOW{i:03d}",
            quantity=1,
            reorder_level=10,
            price=10.0,
        )
        db.add(product)

    await db.commit()

    # Test with limit
    low_stock_products = await Product.get_low_stock_products(db, limit=2)
    assert len(low_stock_products) <= 2

    # Test with skip
    low_stock_products_skip = await Product.get_low_stock_products(db, skip=2, limit=2)
    assert len(low_stock_products_skip) <= 2


@pytest.mark.asyncio
async def test_update_stock_addition(db: AsyncSession):
    """Test updating stock with addition."""
    product = Product(
        name="Stock Test Product",
        sku="STOCK001",
        quantity=50,
        price=10.0,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    initial_quantity = product.quantity

    # Add stock
    updated_product = await product.update_stock(db, quantity_change=25, is_sale=False)

    assert updated_product.quantity == initial_quantity + 25

    # Verify stock movement was created
    movements = await db.execute(
        select(StockMovement).where(StockMovement.product_id == product.id)
    )
    movement = movements.scalar_one()
    assert movement.quantity == 25
    assert movement.movement_type == MovementType.ADDITION


@pytest.mark.asyncio
async def test_update_stock_removal(db: AsyncSession):
    """Test updating stock with removal."""
    product = Product(
        name="Stock Test Product 2",
        sku="STOCK002",
        quantity=50,
        price=10.0,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    initial_quantity = product.quantity

    # Remove stock
    updated_product = await product.update_stock(db, quantity_change=-15, is_sale=False)

    assert updated_product.quantity == initial_quantity - 15

    # Verify stock movement was created
    movements = await db.execute(
        select(StockMovement).where(StockMovement.product_id == product.id)
    )
    movement = movements.scalar_one()
    assert movement.quantity == 15
    assert movement.movement_type == MovementType.REMOVAL


@pytest.mark.asyncio
async def test_update_stock_sale(db: AsyncSession):
    """Test updating stock for a sale."""
    product = Product(
        name="Sale Test Product",
        sku="SALE001",
        quantity=30,
        price=10.0,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    initial_quantity = product.quantity

    # Sale (negative quantity change)
    updated_product = await product.update_stock(db, quantity_change=-5, is_sale=True)

    assert updated_product.quantity == initial_quantity - 5

    # Verify stock movement was created with SALE type
    movements = await db.execute(
        select(StockMovement).where(StockMovement.product_id == product.id)
    )
    movement = movements.scalar_one()
    assert movement.quantity == 5
    assert movement.movement_type == MovementType.SALE


@pytest.mark.asyncio
async def test_update_stock_negative_result(db: AsyncSession):
    """Test updating stock that results in negative quantity."""
    product = Product(
        name="Negative Stock Product",
        sku="NEG001",
        quantity=10,
        price=10.0,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    # Remove more stock than available
    updated_product = await product.update_stock(db, quantity_change=-15, is_sale=False)

    # Should allow negative stock (business decision)
    assert updated_product.quantity == -5


@pytest.mark.asyncio
async def test_product_category_enum():
    """Test ProductCategory enum values."""
    assert ProductCategory.GROCERY.value == "grocery"
    assert ProductCategory.DAIRY.value == "dairy"
    assert ProductCategory.MEAT.value == "meat"
    assert ProductCategory.PRODUCE.value == "produce"
    assert ProductCategory.BAKERY.value == "bakery"
    assert ProductCategory.FROZEN.value == "frozen"
    assert ProductCategory.BEVERAGES.value == "beverages"
    assert ProductCategory.HOUSEHOLD.value == "household"
    assert ProductCategory.PERSONAL_CARE.value == "personal_care"
    assert ProductCategory.OTHER.value == "other"

    # Test enum iteration
    categories = list(ProductCategory)
    assert len(categories) == 10


@pytest.mark.asyncio
async def test_product_supplier_relationship(db: AsyncSession, test_supplier: Supplier):
    """Test product-supplier relationship."""
    product = Product(
        name="Relationship Test Product",
        sku="REL001",
        supplier_id=test_supplier.id,
        price=10.0,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    # Load the relationship
    await db.refresh(product, ["supplier"])

    assert product.supplier is not None
    assert product.supplier.id == test_supplier.id
    assert product.supplier.name == test_supplier.name


@pytest.mark.asyncio
async def test_product_sku_uniqueness(db: AsyncSession):
    """Test that product SKUs must be unique."""
    product1 = Product(
        name="First Product",
        sku="UNIQUE001",
        price=10.0,
    )

    product2 = Product(
        name="Second Product",
        sku="UNIQUE001",  # Same SKU
        price=15.0,
    )

    db.add(product1)
    await db.commit()

    # Adding second product with same SKU should fail
    db.add(product2)
    with pytest.raises(Exception):  # Should raise integrity error
        await db.commit()


@pytest.mark.asyncio
async def test_product_updated_at_on_stock_change(db: AsyncSession):
    """Test that updated_at is modified when stock changes."""
    product = Product(
        name="Update Test Product",
        sku="UPDATE001",
        quantity=20,
        price=10.0,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    original_updated_at = product.updated_at

    # Update stock
    await product.update_stock(db, quantity_change=5, is_sale=False)

    # updated_at should be different
    assert product.updated_at > original_updated_at
