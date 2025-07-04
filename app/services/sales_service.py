from fastapi import HTTPException, status
from sqlalchemy.sql import Select

from app.core.permissions import PermissionRegistry
from app.core.query_manager import QueryManager
from app.models.sales import Order
from app.models.user import User


class OrderQueryManager(QueryManager[Order]):
    """Query manager for Order model."""

    def __init__(self):
        """Initialize with Order model."""
        super().__init__(Order)

    def filter_for_user(self, query: Select, user: User = None) -> Select:
        """
        Filter orders based on user permissions.
        Cashiers can only see their own orders.

        Args:
            query: SQLAlchemy query
            user: User for permission filtering

        Returns:
            Filtered query
        """
        # If no user or user doesn't have read permission, return no orders
        if not user or not PermissionRegistry.has_permission(user, "sales:read"):
            return query.where(False)

        # Admins and managers can see all orders
        if user.is_superuser or PermissionRegistry.has_permission(user, "users:read"):
            return query

        # Cashiers can only see their own orders
        return query.where(Order.cashier_id == user.id)

    def check_create_permission(self, user: User = None) -> None:
        """
        Check if user has permission to create orders.

        Args:
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        if not user or not PermissionRegistry.has_permission(user, "sales:create"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create orders",
            )

    def check_update_permission(self, obj: Order, user: User = None) -> None:
        """
        Check if user has permission to update an order.

        Args:
            obj: Order to update
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authentication required",
            )

        # Check general update permission
        if not PermissionRegistry.has_permission(user, "sales:update"):
            # Cashiers can update their own orders if they have complete permission
            if obj.cashier_id == user.id and PermissionRegistry.has_permission(
                user, "sales:complete"
            ):
                return

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update orders",
            )

    def check_delete_permission(self, obj: Order, user: User = None) -> None:
        """
        Check if user has permission to delete an order.
        Orders should not be deleted, only cancelled or refunded.

        Args:
            obj: Order to delete
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        # Orders should not be deleted
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Orders cannot be deleted, use cancel or refund instead",
        )


# Create instance for use in API routes
order_manager = OrderQueryManager()
