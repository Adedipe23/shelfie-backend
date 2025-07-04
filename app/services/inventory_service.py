from fastapi import HTTPException, status
from sqlalchemy.sql import Select

from app.core.permissions import PermissionRegistry
from app.core.query_manager import QueryManager
from app.models.inventory import Product, Supplier
from app.models.user import User


class ProductQueryManager(QueryManager[Product]):
    """Query manager for Product model."""

    def __init__(self):
        """Initialize with Product model."""
        super().__init__(Product)

    def filter_for_user(self, query: Select, user: User = None) -> Select:
        """
        Filter products based on user permissions.
        All users can read products, but with different levels of detail.

        Args:
            query: SQLAlchemy query
            user: User for permission filtering

        Returns:
            Filtered query
        """
        # If user has read permission, return all products
        if user and PermissionRegistry.has_permission(user, "inventory:read"):
            return query

        # If no user or no permission, return no products
        return query.where(False)

    def check_create_permission(self, user: User = None) -> None:
        """
        Check if user has permission to create products.

        Args:
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        if not user or not PermissionRegistry.has_permission(user, "inventory:create"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create products",
            )

    def check_update_permission(self, obj: Product, user: User = None) -> None:
        """
        Check if user has permission to update a product.

        Args:
            obj: Product to update
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        if not user or not PermissionRegistry.has_permission(user, "inventory:update"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update products",
            )

    def check_delete_permission(self, obj: Product, user: User = None) -> None:
        """
        Check if user has permission to delete a product.

        Args:
            obj: Product to delete
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        if not user or not PermissionRegistry.has_permission(user, "inventory:delete"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete products",
            )


class SupplierQueryManager(QueryManager[Supplier]):
    """Query manager for Supplier model."""

    def __init__(self):
        """Initialize with Supplier model."""
        super().__init__(Supplier)

    def filter_for_user(self, query: Select, user: User = None) -> Select:
        """
        Filter suppliers based on user permissions.

        Args:
            query: SQLAlchemy query
            user: User for permission filtering

        Returns:
            Filtered query
        """
        # If user has read permission, return all suppliers
        if user and PermissionRegistry.has_permission(user, "inventory:read"):
            return query

        # If no user or no permission, return no suppliers
        return query.where(False)

    def check_create_permission(self, user: User = None) -> None:
        """
        Check if user has permission to create suppliers.

        Args:
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        if not user or not PermissionRegistry.has_permission(user, "inventory:create"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create suppliers",
            )

    def check_update_permission(self, obj: Supplier, user: User = None) -> None:
        """
        Check if user has permission to update a supplier.

        Args:
            obj: Supplier to update
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        if not user or not PermissionRegistry.has_permission(user, "inventory:update"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update suppliers",
            )

    def check_delete_permission(self, obj: Supplier, user: User = None) -> None:
        """
        Check if user has permission to delete a supplier.

        Args:
            obj: Supplier to delete
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        if not user or not PermissionRegistry.has_permission(user, "inventory:delete"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete suppliers",
            )


# Create instances for use in API routes
product_manager = ProductQueryManager()
supplier_manager = SupplierQueryManager()
