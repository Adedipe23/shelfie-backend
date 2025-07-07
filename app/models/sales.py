from datetime import datetime
from enum import Enum
from typing import ClassVar, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import Field, Relationship

from app.models.base import BaseModel
from app.models.inventory import Product


class PaymentMethod(str, Enum):
    """Payment method enumeration."""

    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    MOBILE_PAYMENT = "mobile_payment"
    OTHER = "other"


class OrderStatus(str, Enum):
    """Order status enumeration."""

    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(BaseModel, table=True):
    """Order model for sales management."""

    __tablename__: ClassVar[str] = "orders"

    customer_name: str = Field(default="")
    total_amount: float = Field(default=0.0)
    payment_method: PaymentMethod = Field(default=PaymentMethod.CASH)
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    cashier_id: Optional[int] = Field(default=None, foreign_key="users.id")

    # Relationships
    items: List["OrderItem"] = Relationship(back_populates="order")

    @classmethod
    async def get_by_id(cls, db: AsyncSession, id: int) -> Optional["Order"]:
        """Get an order by ID with items preloaded."""
        query = select(cls).where(cls.id == id).options(selectinload(cls.items))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_all(
        cls, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List["Order"]:
        """Get all orders with items preloaded."""
        query = select(cls).options(selectinload(cls.items)).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_date_range(
        cls,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List["Order"]:
        """Get orders within a date range."""
        query = (
            select(cls)
            .where(cls.created_at >= start_date)
            .where(cls.created_at <= end_date)
            .options(selectinload(cls.items))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def calculate_total(self, db: AsyncSession) -> float:
        """Calculate the total amount of the order."""
        # Explicitly load order items to avoid lazy loading issues
        query = select(OrderItem).where(OrderItem.order_id == self.id)
        result = await db.execute(query)
        items = result.scalars().all()

        total = 0.0
        for item in items:
            total += item.quantity * item.unit_price

        self.total_amount = total
        db.add(self)
        await db.commit()
        await db.refresh(self)
        return total

    async def complete(self, db: AsyncSession) -> "Order":
        """Complete the order and update inventory."""
        if self.status != OrderStatus.PENDING:
            return self

        # Update order status
        self.status = OrderStatus.COMPLETED
        db.add(self)

        # Explicitly load order items to avoid lazy loading issues
        query = select(OrderItem).where(OrderItem.order_id == self.id)
        result = await db.execute(query)
        items = result.scalars().all()

        # Update inventory for each item
        for item in items:
            product = await Product.get_by_id(db, id=item.product_id)
            if product:
                await product.update_stock(db, -item.quantity, is_sale=True)

        await db.commit()
        await db.refresh(self)
        return self

    async def cancel(self, db: AsyncSession) -> "Order":
        """Cancel the order."""
        if self.status != OrderStatus.PENDING:
            return self

        self.status = OrderStatus.CANCELLED
        db.add(self)
        await db.commit()
        await db.refresh(self)
        return self

    async def refund(self, db: AsyncSession) -> "Order":
        """Refund the order and update inventory."""
        if self.status != OrderStatus.COMPLETED:
            return self

        # Update order status
        self.status = OrderStatus.REFUNDED
        db.add(self)

        # Explicitly load order items to avoid lazy loading issues
        query = select(OrderItem).where(OrderItem.order_id == self.id)
        result = await db.execute(query)
        items = result.scalars().all()

        # Update inventory for each item
        for item in items:
            product = await Product.get_by_id(db, id=item.product_id)
            if product:
                await product.update_stock(db, item.quantity, is_sale=False)

        await db.commit()
        await db.refresh(self)
        return self


class OrderItem(BaseModel, table=True):
    """Order item model for sales management."""

    __tablename__: ClassVar[str] = "order_items"

    order_id: int = Field(foreign_key="orders.id")
    product_id: int = Field(foreign_key="products.id")
    quantity: int = Field(default=1)
    unit_price: float = Field(default=0.0)

    # Relationships
    order: Order = Relationship(back_populates="items")
    product: Product = Relationship()
