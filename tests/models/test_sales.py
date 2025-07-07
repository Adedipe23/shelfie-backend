"""
Tests for sales models.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Product, ProductCategory
from app.models.sales import Order, OrderItem, OrderStatus, PaymentMethod
from app.models.user import User, UserRole


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_creation(db: AsyncSession):
    """Test basic order creation."""
    order = Order(
        customer_name="John Doe",
        total_amount=100.0,
        payment_method=PaymentMethod.CASH,
        status=OrderStatus.PENDING,
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    assert order.id is not None
    assert order.customer_name == "John Doe"
    assert order.total_amount == 100.0
    assert order.payment_method == PaymentMethod.CASH
    assert order.status == OrderStatus.PENDING
    assert order.created_at is not None
    assert order.updated_at is not None


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_creation_with_defaults(db: AsyncSession):
    """Test order creation with default values."""
    order = Order()

    db.add(order)
    await db.commit()
    await db.refresh(order)

    assert order.customer_name == ""
    assert order.total_amount == 0.0
    assert order.payment_method == PaymentMethod.CASH
    assert order.status == OrderStatus.PENDING
    assert order.cashier_id is None


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_with_cashier(db: AsyncSession):
    """Test order creation with cashier."""
    # Create a cashier user
    cashier = User(
        email="cashier@example.com",
        hashed_password="hashed_password",
        full_name="Cashier User",
        role=UserRole.CASHIER.value,
    )

    db.add(cashier)
    await db.commit()
    await db.refresh(cashier)

    # Create order with cashier
    order = Order(
        customer_name="Jane Doe",
        total_amount=50.0,
        payment_method=PaymentMethod.CREDIT_CARD,
        cashier_id=cashier.id,
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    assert order.cashier_id == cashier.id


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_item_creation(db: AsyncSession):
    """Test order item creation."""
    # Create a product
    product = Product(
        name="Test Product",
        sku="TEST001",
        price=10.0,
        quantity=100,
        category=ProductCategory.HOUSEHOLD,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    # Create an order
    order = Order(customer_name="Test Customer")

    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Create order item
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=2,
        unit_price=10.0,
    )

    db.add(order_item)
    await db.commit()
    await db.refresh(order_item)

    assert order_item.id is not None
    assert order_item.order_id == order.id
    assert order_item.product_id == product.id
    assert order_item.quantity == 2
    assert order_item.unit_price == 10.0


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_item_defaults(db: AsyncSession):
    """Test order item creation with defaults."""
    # Create a product and order first
    product = Product(
        name="Test Product",
        sku="TEST002",
        price=15.0,
        quantity=50,
        category=ProductCategory.GROCERY,
    )

    order = Order(customer_name="Test Customer")

    db.add(product)
    db.add(order)
    await db.commit()
    await db.refresh(product)
    await db.refresh(order)

    # Create order item with defaults
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
    )

    db.add(order_item)
    await db.commit()
    await db.refresh(order_item)

    assert order_item.quantity == 1
    assert order_item.unit_price == 0.0


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_get_by_id(db: AsyncSession):
    """Test getting order by ID with items preloaded."""
    # Create a product and order
    product = Product(
        name="Test Product",
        sku="TEST003",
        price=20.0,
        quantity=30,
        category=ProductCategory.PERSONAL_CARE,
    )

    order = Order(customer_name="Test Customer")

    db.add(product)
    db.add(order)
    await db.commit()
    await db.refresh(product)
    await db.refresh(order)

    # Create order item
    order_item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=3,
        unit_price=20.0,
    )

    db.add(order_item)
    await db.commit()

    # Test get_by_id
    retrieved_order = await Order.get_by_id(db, order.id)
    assert retrieved_order is not None
    assert retrieved_order.id == order.id
    assert retrieved_order.customer_name == "Test Customer"
    assert len(retrieved_order.items) == 1
    assert retrieved_order.items[0].quantity == 3


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_get_by_id_not_found(db: AsyncSession):
    """Test getting non-existent order by ID."""
    result = await Order.get_by_id(db, 99999)
    assert result is None


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_get_all(db: AsyncSession):
    """Test getting all orders."""
    # Create multiple orders
    orders = []
    for i in range(3):
        order = Order(customer_name=f"Customer {i}")
        orders.append(order)
        db.add(order)

    await db.commit()

    # Test get_all
    all_orders = await Order.get_all(db)
    assert len(all_orders) >= 3  # At least our test orders

    # Test pagination
    paginated_orders = await Order.get_all(db, skip=0, limit=2)
    assert len(paginated_orders) == 2


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_get_by_date_range(db: AsyncSession):
    """Test getting orders by date range."""
    # Create orders with different dates
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)

    # Convert to naive datetime for database compatibility
    yesterday_naive = yesterday.replace(tzinfo=None)
    tomorrow_naive = tomorrow.replace(tzinfo=None)

    # Create an order (will have current timestamp)
    order = Order(customer_name="Recent Customer")
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Test date range query
    orders = await Order.get_by_date_range(db, yesterday_naive, tomorrow_naive)
    assert len(orders) >= 1

    # Test with narrow date range (should find nothing)
    future_start = now + timedelta(days=2)
    future_end = now + timedelta(days=3)
    future_start_naive = future_start.replace(tzinfo=None)
    future_end_naive = future_end.replace(tzinfo=None)
    future_orders = await Order.get_by_date_range(
        db, future_start_naive, future_end_naive
    )
    assert len(future_orders) == 0


@pytest.mark.models
@pytest.mark.asyncio
async def test_payment_method_enum():
    """Test PaymentMethod enum values."""
    assert PaymentMethod.CASH == "cash"
    assert PaymentMethod.CREDIT_CARD == "credit_card"
    assert PaymentMethod.DEBIT_CARD == "debit_card"
    assert PaymentMethod.MOBILE_PAYMENT == "mobile_payment"
    assert PaymentMethod.OTHER == "other"


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_status_enum():
    """Test OrderStatus enum values."""
    assert OrderStatus.PENDING == "pending"
    assert OrderStatus.COMPLETED == "completed"
    assert OrderStatus.CANCELLED == "cancelled"
    assert OrderStatus.REFUNDED == "refunded"


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_calculate_total(db: AsyncSession):
    """Test order total calculation."""
    # Create products
    product1 = Product(
        name="Product 1",
        sku="CALC001",
        price=10.0,
        quantity=100,
        category=ProductCategory.HOUSEHOLD,
    )

    product2 = Product(
        name="Product 2",
        sku="CALC002",
        price=25.0,
        quantity=50,
        category=ProductCategory.GROCERY,
    )

    db.add(product1)
    db.add(product2)
    await db.commit()
    await db.refresh(product1)
    await db.refresh(product2)

    # Create order
    order = Order(customer_name="Calculate Customer")
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Create order items
    item1 = OrderItem(
        order_id=order.id,
        product_id=product1.id,
        quantity=2,
        unit_price=10.0,
    )

    item2 = OrderItem(
        order_id=order.id,
        product_id=product2.id,
        quantity=3,
        unit_price=25.0,
    )

    db.add(item1)
    db.add(item2)
    await db.commit()

    # Calculate total
    total = await order.calculate_total(db)

    # Expected: (2 * 10.0) + (3 * 25.0) = 20.0 + 75.0 = 95.0
    assert total == 95.0
    assert order.total_amount == 95.0


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_complete(db: AsyncSession):
    """Test order completion and inventory update."""
    # Create product with stock
    product = Product(
        name="Complete Product",
        sku="COMP001",
        price=15.0,
        quantity=100,
        category=ProductCategory.HOUSEHOLD,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)
    initial_stock = product.quantity

    # Create order
    order = Order(
        customer_name="Complete Customer",
        status=OrderStatus.PENDING,
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Create order item
    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=5,
        unit_price=15.0,
    )

    db.add(item)
    await db.commit()

    # Complete the order
    completed_order = await order.complete(db)

    assert completed_order.status == OrderStatus.COMPLETED

    # Check inventory was updated
    await db.refresh(product)
    assert product.quantity == initial_stock - 5


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_complete_already_completed(db: AsyncSession):
    """Test completing an already completed order."""
    order = Order(
        customer_name="Already Complete Customer",
        status=OrderStatus.COMPLETED,
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Try to complete again
    result = await order.complete(db)

    # Should return the order unchanged
    assert result.status == OrderStatus.COMPLETED
    assert result.id == order.id


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_cancel(db: AsyncSession):
    """Test order cancellation."""
    order = Order(
        customer_name="Cancel Customer",
        status=OrderStatus.PENDING,
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Cancel the order
    cancelled_order = await order.cancel(db)

    assert cancelled_order.status == OrderStatus.CANCELLED


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_cancel_already_completed(db: AsyncSession):
    """Test cancelling an already completed order."""
    order = Order(
        customer_name="Cannot Cancel Customer",
        status=OrderStatus.COMPLETED,
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Try to cancel
    result = await order.cancel(db)

    # Should return the order unchanged
    assert result.status == OrderStatus.COMPLETED


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_refund(db: AsyncSession):
    """Test order refund and inventory restoration."""
    # Create product with stock
    product = Product(
        name="Refund Product",
        sku="REF001",
        price=20.0,
        quantity=50,
        category=ProductCategory.PERSONAL_CARE,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    # Simulate a completed order that reduced stock
    original_stock = product.quantity
    await product.update_stock(db, -10, is_sale=True)  # Reduce stock by 10
    await db.refresh(product)
    reduced_stock = product.quantity

    # Create completed order
    order = Order(
        customer_name="Refund Customer",
        status=OrderStatus.COMPLETED,
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Create order item
    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=10,
        unit_price=20.0,
    )

    db.add(item)
    await db.commit()

    # Refund the order
    refunded_order = await order.refund(db)

    assert refunded_order.status == OrderStatus.REFUNDED

    # Check inventory was restored
    await db.refresh(product)
    assert product.quantity == reduced_stock + 10


@pytest.mark.models
@pytest.mark.asyncio
async def test_order_refund_not_completed(db: AsyncSession):
    """Test refunding a non-completed order."""
    order = Order(
        customer_name="Cannot Refund Customer",
        status=OrderStatus.PENDING,
    )

    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Try to refund
    result = await order.refund(db)

    # Should return the order unchanged
    assert result.status == OrderStatus.PENDING
