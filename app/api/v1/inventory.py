from typing import Any, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.inventory import Product, Supplier
from app.models.user import User, UserRole
from app.schemas.inventory import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    StockUpdate,
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
)
from app.tasks.notifications import send_low_stock_notifications

router = APIRouter()


# Product routes
@router.get("/products", response_model=List[ProductResponse])
async def read_products(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve products.
    """
    products = await Product.get_all(db, skip=skip, limit=limit)
    return products


@router.post("/products", response_model=ProductResponse)
async def create_product(
    *,
    db: AsyncSession = Depends(get_db),
    product_in: ProductCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create new product.
    """
    if current_user.role == UserRole.CASHIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    product = await Product.get_by_sku(db, sku=product_in.sku)
    if product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A product with this SKU already exists",
        )

    product = await Product.create(db, obj_in=product_in.model_dump())
    return product


@router.get("/products/low-stock", response_model=List[ProductResponse])
async def read_low_stock_products(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve products with stock below reorder level.
    """
    if current_user.role == UserRole.CASHIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    products = await Product.get_low_stock_products(db, skip=skip, limit=limit)
    return products


@router.get("/products/{product_id}", response_model=ProductResponse)
async def read_product(
    *,
    db: AsyncSession = Depends(get_db),
    product_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a specific product by id.
    """
    product = await Product.get_by_id(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    *,
    db: AsyncSession = Depends(get_db),
    product_id: int,
    product_in: ProductUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a product.
    """
    if current_user.role == UserRole.CASHIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    product = await Product.get_by_id(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    product_data = product_in.model_dump(exclude_unset=True)
    if product_data:
        product = await product.update(db, product_data)

    return product


@router.delete("/products/{product_id}", response_model=ProductResponse)
async def delete_product(
    *,
    db: AsyncSession = Depends(get_db),
    product_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a product.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    product = await Product.get_by_id(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    await product.delete(db)
    return product


@router.put("/products/{product_id}/stock", response_model=ProductResponse)
async def update_product_stock(
    *,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks,
    product_id: int,
    stock_update: StockUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update product stock.
    """
    product = await Product.get_by_id(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Check if this would result in negative stock
    if product.quantity + stock_update.quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reduce stock below zero",
        )

    # Update stock
    product = await product.update_stock(db, stock_update.quantity)

    # Check if stock is low and send notification if needed
    if product.quantity <= product.reorder_level:
        # In a real app, you would get this from a settings table or similar
        manager_emails = ["manager@example.com"]

        # Send low stock notification as a background task
        send_low_stock_notifications(
            background_tasks,
            emails=manager_emails,
            product_name=product.name,
            current_stock=product.quantity,
        )

    return product


# Supplier routes
@router.get("/suppliers", response_model=List[SupplierResponse])
async def read_suppliers(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Retrieve suppliers.
    """
    suppliers = await Supplier.get_all(db, skip=skip, limit=limit)
    return suppliers


@router.post("/suppliers", response_model=SupplierResponse)
async def create_supplier(
    *,
    db: AsyncSession = Depends(get_db),
    supplier_in: SupplierCreate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create new supplier.
    """
    if current_user.role == UserRole.CASHIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    supplier = await Supplier.create(db, obj_in=supplier_in.model_dump())
    return supplier


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def read_supplier(
    *,
    db: AsyncSession = Depends(get_db),
    supplier_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get a specific supplier by id.
    """
    supplier = await Supplier.get_by_id(db, id=supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    return supplier


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    *,
    db: AsyncSession = Depends(get_db),
    supplier_id: int,
    supplier_in: SupplierUpdate,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update a supplier.
    """
    if current_user.role == UserRole.CASHIER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    supplier = await Supplier.get_by_id(db, id=supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    supplier_data = supplier_in.model_dump(exclude_unset=True)
    if supplier_data:
        supplier = await supplier.update(db, supplier_data)

    return supplier


@router.delete("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def delete_supplier(
    *,
    db: AsyncSession = Depends(get_db),
    supplier_id: int,
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Delete a supplier.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    supplier = await Supplier.get_by_id(db, id=supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found",
        )

    await supplier.delete(db)
    return supplier
