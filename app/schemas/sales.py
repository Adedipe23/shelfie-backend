from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.sales import OrderStatus, PaymentMethod


# Order item schemas
class OrderItemBase(BaseModel):
    """Base order item schema with shared properties."""

    product_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None


class OrderItemCreate(OrderItemBase):
    """Order item creation schema."""

    product_id: int
    quantity: int = Field(gt=0)
    unit_price: Optional[float] = (
        None  # If not provided, will use current product price
    )


class OrderItemResponse(OrderItemBase):
    """Order item response schema."""

    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float

    model_config = ConfigDict(from_attributes=True)


# Order schemas
class OrderBase(BaseModel):
    """Base order schema with shared properties."""

    customer_name: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    cashier_id: Optional[int] = None


class OrderCreate(OrderBase):
    """Order creation schema."""

    customer_name: str = ""
    payment_method: PaymentMethod = PaymentMethod.CASH
    items: List[OrderItemCreate]


class OrderUpdate(OrderBase):
    """Order update schema."""

    status: Optional[OrderStatus] = None


class OrderResponse(OrderBase):
    """Order response schema."""

    id: int
    customer_name: str
    total_amount: float
    payment_method: PaymentMethod
    status: OrderStatus
    cashier_id: Optional[int]
    created_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


# Sales report schemas
class DateRangeRequest(BaseModel):
    """Date range request schema for sales reports."""

    start_date: datetime
    end_date: datetime


class SalesSummary(BaseModel):
    """Sales summary schema for reports."""

    total_sales: float
    order_count: int
    average_order_value: float
    start_date: datetime
    end_date: datetime
