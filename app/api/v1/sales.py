from datetime import timedelta
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.inventory import Product
from app.models.sales import Order, OrderItem, OrderStatus
from app.models.user import User, UserRole
from app.schemas.sales import (
    DateRangeRequest,
    OrderCreate,
    OrderItemResponse,
    OrderResponse,
    OrderUpdate,
    SalesSummary,
)
from app.utils.datetime_utils import ensure_naive_for_db, now_utc

router = APIRouter()


async def get_order_with_items(db: AsyncSession, order: Order) -> OrderResponse:
    """
    Helper function to get order items and create an OrderResponse.
    This avoids lazy loading issues during response serialization.
    """
    # Explicitly load order items
    query = select(OrderItem).where(OrderItem.order_id == order.id)
    result = await db.execute(query)
    items = result.scalars().all()

    # Create OrderItemResponse objects
    item_responses = [
        OrderItemResponse(
            id=item.id,
            order_id=item.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        for item in items
    ]

    # Create OrderResponse
    return OrderResponse(
        id=order.id,
        customer_name=order.customer_name,
        total_amount=order.total_amount,
        payment_method=order.payment_method,
        status=order.status,
        cashier_id=order.cashier_id,
        created_at=order.created_at,
        items=item_responses,
    )


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    *,
    db: AsyncSession = Depends(get_db),
    order_in: OrderCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new order.
    """
    # Create order
    order_data = order_in.model_dump(exclude={"items"})
    order_data["cashier_id"] = current_user.id
    order = await Order.create(db, obj_in=order_data)

    # Create order items
    for item_data in order_in.items:
        # Get product
        product = await Product.get_by_id(db, id=item_data.product_id)
        if not product:
            await order.delete(db)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item_data.product_id} not found",
            )

        # Check stock
        if product.quantity < item_data.quantity:
            await order.delete(db)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.name}",
            )

        # Use product price if not provided
        unit_price = item_data.unit_price or product.price

        # Create order item
        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item_data.quantity,
            unit_price=unit_price,
        )
        db.add(item)

    await db.commit()
    await db.refresh(order)

    # Calculate total
    await order.calculate_total(db)

    # Return order response with items
    return await get_order_with_items(db, order)


@router.get("/orders", response_model=List[OrderResponse])
async def read_orders(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve orders.
    """
    orders = await Order.get_all(db, skip=skip, limit=limit)

    # Convert each order to OrderResponse with items
    order_responses = []
    for order in orders:
        order_response = await get_order_with_items(db, order)
        order_responses.append(order_response)

    return order_responses


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def read_order(
    *,
    db: AsyncSession = Depends(get_db),
    order_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a specific order by id.
    """
    order = await Order.get_by_id(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Return order response with items
    return await get_order_with_items(db, order)


@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    *,
    db: AsyncSession = Depends(get_db),
    order_id: int,
    order_in: OrderUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update an order.
    """
    order = await Order.get_by_id(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    order_data = order_in.model_dump(exclude_unset=True)
    if order_data:
        order = await order.update(db, order_data)

    # Return order response with items
    return await get_order_with_items(db, order)


@router.post("/orders/{order_id}/complete", response_model=OrderResponse)
async def complete_order(
    *,
    db: AsyncSession = Depends(get_db),
    order_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Complete an order and update inventory.
    """
    order = await Order.get_by_id(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is already {order.status}",
        )

    order = await order.complete(db)

    # Return order response with items
    return await get_order_with_items(db, order)


@router.post("/orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    *,
    db: AsyncSession = Depends(get_db),
    order_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Cancel an order.
    """
    order = await Order.get_by_id(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is already {order.status}",
        )

    order = await order.cancel(db)

    # Return order response with items
    return await get_order_with_items(db, order)


@router.post("/orders/{order_id}/refund", response_model=OrderResponse)
async def refund_order(
    *,
    db: AsyncSession = Depends(get_db),
    order_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Refund an order and update inventory.
    """
    if current_user.role == UserRole.CASHIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    order = await Order.get_by_id(db, id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status != OrderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only completed orders can be refunded",
        )

    order = await order.refund(db)

    # Return order response with items
    return await get_order_with_items(db, order)


@router.post("/reports/sales", response_model=SalesSummary)
async def generate_sales_report(
    *,
    db: AsyncSession = Depends(get_db),
    date_range: DateRangeRequest,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Generate a sales report for a date range.
    """
    if current_user.role == UserRole.CASHIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Convert timezone-aware dates to naive for database compatibility
    start_date_naive = ensure_naive_for_db(date_range.start_date)
    end_date_naive = ensure_naive_for_db(date_range.end_date)

    # Get orders in date range
    orders = await Order.get_by_date_range(
        db,
        start_date=start_date_naive,
        end_date=end_date_naive,
    )

    # Calculate summary - only use completed orders
    completed_orders = [
        order for order in orders if order.status == OrderStatus.COMPLETED
    ]

    # Calculate total sales by summing up the items for each order
    total_sales = 0.0
    for order in completed_orders:
        # Calculate total for this order from its items
        order_total = 0.0
        for item in order.items:
            order_total += item.quantity * item.unit_price
        total_sales += order_total

    order_count = len(completed_orders)
    average_order_value = total_sales / order_count if order_count > 0 else 0

    return SalesSummary(
        total_sales=total_sales,
        order_count=order_count,
        average_order_value=average_order_value,
        start_date=date_range.start_date,
        end_date=date_range.end_date,
    )


@router.get("/reports/daily-sales")
async def get_daily_sales(
    *,
    db: AsyncSession = Depends(get_db),
    days: int = 7,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get daily sales for the last N days.
    """
    if current_user.role == UserRole.CASHIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Calculate date range
    end_date = now_utc()
    start_date = end_date - timedelta(days=days)

    # Convert to naive datetime for database compatibility
    start_date_naive = ensure_naive_for_db(start_date)
    end_date_naive = ensure_naive_for_db(end_date)

    # Get orders in date range
    orders = await Order.get_by_date_range(
        db,
        start_date=start_date_naive,
        end_date=end_date_naive,
        limit=1000,  # Higher limit for reports
    )

    # Filter completed orders first to avoid any potential lazy loading issues
    completed_orders = [
        order for order in orders if order.status == OrderStatus.COMPLETED
    ]

    # Group by day
    daily_sales = {}
    for order in completed_orders:
        day = order.created_at.date().isoformat()
        if day not in daily_sales:
            daily_sales[day] = {
                "date": day,
                "total_sales": 0,
                "order_count": 0,
            }

        # Calculate total for this order from its items
        order_total = 0.0
        for item in order.items:
            order_total += item.quantity * item.unit_price

        daily_sales[day]["total_sales"] += order_total
        daily_sales[day]["order_count"] += 1

    return list(daily_sales.values())
