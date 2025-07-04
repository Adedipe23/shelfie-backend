from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional

from sqlalchemy import Column, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, Relationship

from app.models.base import BaseModel


class ProductCategory(str, Enum):
    """Product category enumeration."""

    GROCERY = "grocery"
    DAIRY = "dairy"
    MEAT = "meat"
    PRODUCE = "produce"
    BAKERY = "bakery"
    FROZEN = "frozen"
    BEVERAGES = "beverages"
    HOUSEHOLD = "household"
    PERSONAL_CARE = "personal_care"
    OTHER = "other"


class Product(BaseModel, table=True):
    """Product model for inventory management."""

    __tablename__: ClassVar[str] = "products"

    name: str = Field(nullable=False)
    description: str = Field(default="")
    sku: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    category: ProductCategory = Field(default=ProductCategory.OTHER)
    price: float = Field(default=0.0)
    cost: float = Field(default=0.0)
    quantity: int = Field(default=0)
    reorder_level: int = Field(default=10)
    supplier_id: Optional[int] = Field(default=None, foreign_key="suppliers.id")

    # Relationships
    supplier: Optional["Supplier"] = Relationship(back_populates="products")

    @classmethod
    async def get_by_sku(cls, db: AsyncSession, sku: str) -> Optional["Product"]:
        """Get a product by SKU."""
        query = select(cls).where(cls.sku == sku)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_low_stock_products(
        cls, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> list["Product"]:
        """Get products with stock below reorder level."""
        query = (
            select(cls)
            .where(cls.quantity <= cls.reorder_level)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def update_stock(
        self, db: AsyncSession, quantity_change: int, is_sale: bool = False
    ) -> "Product":
        """
        Update product stock.

        Args:
            db: Database session
            quantity_change: Amount to change (positive for additions, negative for removals)
            is_sale: Whether this is a sale transaction

        Returns:
            Updated product
        """
        self.quantity += quantity_change
        self.updated_at = datetime.now()

        # Create stock movement record
        movement = StockMovement(
            product_id=self.id,
            quantity=abs(quantity_change),
            movement_type=(
                MovementType.SALE
                if is_sale
                else (
                    MovementType.ADDITION
                    if quantity_change > 0
                    else MovementType.REMOVAL
                )
            ),
        )
        db.add(movement)

        db.add(self)
        await db.commit()
        await db.refresh(self)
        return self


class Supplier(BaseModel, table=True):
    """Supplier model for inventory management."""

    __tablename__: ClassVar[str] = "suppliers"

    name: str = Field(nullable=False)
    contact_name: str = Field(default="")
    email: str = Field(default="")
    phone: str = Field(default="")
    address: str = Field(default="")

    # Relationships
    products: list[Product] = Relationship(back_populates="supplier")


class MovementType(str, Enum):
    """Stock movement type enumeration."""

    ADDITION = "addition"
    REMOVAL = "removal"
    SALE = "sale"
    RETURN = "return"
    ADJUSTMENT = "adjustment"


class StockMovement(BaseModel, table=True):
    """Stock movement model for tracking inventory changes."""

    __tablename__: ClassVar[str] = "stock_movements"

    product_id: int = Field(foreign_key="products.id")
    quantity: int = Field(default=0)
    movement_type: MovementType = Field(default=MovementType.ADDITION)
    notes: str = Field(default="")
