from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.inventory import MovementType, ProductCategory


# Product schemas
class ProductBase(BaseModel):
    """Base product schema with shared properties."""

    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[ProductCategory] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    quantity: Optional[int] = None
    reorder_level: Optional[int] = None
    supplier_id: Optional[int] = None


class ProductCreate(ProductBase):
    """Product creation schema."""

    name: str
    sku: str
    price: float = Field(ge=0)
    cost: float = Field(ge=0)
    quantity: int = Field(ge=0, default=0)


class ProductUpdate(ProductBase):
    """Product update schema."""


class ProductResponse(ProductBase):
    """Product response schema."""

    id: int
    name: str
    sku: str
    category: ProductCategory
    price: float
    cost: float
    quantity: int
    reorder_level: int

    model_config = ConfigDict(from_attributes=True)


# Supplier schemas
class SupplierBase(BaseModel):
    """Base supplier schema with shared properties."""

    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class SupplierCreate(SupplierBase):
    """Supplier creation schema."""

    name: str


class SupplierUpdate(SupplierBase):
    """Supplier update schema."""


class SupplierResponse(SupplierBase):
    """Supplier response schema."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# Stock movement schemas
class StockMovementBase(BaseModel):
    """Base stock movement schema with shared properties."""

    product_id: Optional[int] = None
    quantity: Optional[int] = None
    movement_type: Optional[MovementType] = None
    notes: Optional[str] = None


class StockMovementCreate(StockMovementBase):
    """Stock movement creation schema."""

    product_id: int
    quantity: int = Field(gt=0)
    movement_type: MovementType
    notes: Optional[str] = None


class StockMovementResponse(StockMovementBase):
    """Stock movement response schema."""

    id: int
    product_id: int
    quantity: int
    movement_type: MovementType
    created_at: str

    model_config = ConfigDict(from_attributes=True)


# Stock update schema
class StockUpdate(BaseModel):
    """Schema for updating product stock."""

    quantity: int = Field(description="Quantity to add (positive) or remove (negative)")
    notes: Optional[str] = None
