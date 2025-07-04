from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.base import BaseModel
from app.models.user import User

# Type variable for the model
T = TypeVar("T", bound=BaseModel)


class QueryManager(Generic[T]):
    """
    Query manager for handling model queries with permission filtering.
    Similar to Django's QuerySet manager.
    """

    def __init__(self, model: Type[T]):
        """Initialize with model class."""
        self.model = model

    async def get_by_id(
        self, db: AsyncSession, id: int, user: Optional[User] = None
    ) -> Optional[T]:
        """
        Get a record by ID with permission filtering.

        Args:
            db: Database session
            id: Record ID
            user: User for permission filtering

        Returns:
            Optional record
        """
        query = select(self.model).where(self.model.id == id)
        query = self.filter_for_user(query, user)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        user: Optional[User] = None,
    ) -> List[T]:
        """
        Get all records with pagination and permission filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            user: User for permission filtering

        Returns:
            List of records
        """
        query = select(self.model).offset(skip).limit(limit)
        query = self.filter_for_user(query, user)
        result = await db.execute(query)
        return result.scalars().all()

    async def create(
        self, db: AsyncSession, obj_in: Dict[str, Any], user: Optional[User] = None
    ) -> T:
        """
        Create a new record with permission check.

        Args:
            db: Database session
            obj_in: Data for creating the record
            user: User for permission check

        Returns:
            Created record
        """
        self.check_create_permission(user)

        obj = self.model(**obj_in)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(
        self,
        db: AsyncSession,
        db_obj: T,
        obj_in: Dict[str, Any],
        user: Optional[User] = None,
    ) -> T:
        """
        Update a record with permission check.

        Args:
            db: Database session
            db_obj: Record to update
            obj_in: Data for updating the record
            user: User for permission check

        Returns:
            Updated record
        """
        self.check_update_permission(db_obj, user)

        for key, value in obj_in.items():
            setattr(db_obj, key, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(
        self, db: AsyncSession, db_obj: T, user: Optional[User] = None
    ) -> T:
        """
        Delete a record with permission check.

        Args:
            db: Database session
            db_obj: Record to delete
            user: User for permission check

        Returns:
            Deleted record
        """
        self.check_delete_permission(db_obj, user)

        await db.delete(db_obj)
        await db.commit()
        return db_obj

    def filter_for_user(self, query: Select, user: Optional[User] = None) -> Select:
        """
        Filter query based on user permissions.
        Override this method in subclasses to implement specific filtering.

        Args:
            query: SQLAlchemy query
            user: User for permission filtering

        Returns:
            Filtered query
        """
        # By default, no filtering
        return query

    def check_create_permission(self, user: Optional[User] = None) -> None:
        """
        Check if user has permission to create records.
        Override this method in subclasses to implement specific checks.

        Args:
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        # By default, allow creation

    def check_update_permission(self, obj: T, user: Optional[User] = None) -> None:
        """
        Check if user has permission to update a record.
        Override this method in subclasses to implement specific checks.

        Args:
            obj: Record to update
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        # By default, allow updates

    def check_delete_permission(self, obj: T, user: Optional[User] = None) -> None:
        """
        Check if user has permission to delete a record.
        Override this method in subclasses to implement specific checks.

        Args:
            obj: Record to delete
            user: User for permission check

        Raises:
            HTTPException: If user doesn't have permission
        """
        # By default, allow deletion
