from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel

T = TypeVar("T", bound="BaseModel")


class BaseModel(SQLModel):
    """Base model with common fields and methods."""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Class variables
    __tablename__: ClassVar[str]

    @classmethod
    async def get_by_id(cls: Type[T], db: AsyncSession, id: int) -> Optional[T]:
        """Get a record by ID."""
        query = select(cls).where(cls.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_all(
        cls: Type[T], db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[T]:
        """Get all records with pagination."""
        query = select(cls).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls: Type[T], db: AsyncSession, obj_in: Dict[str, Any]) -> T:
        """Create a new record."""
        obj = cls(**obj_in)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(self: T, db: AsyncSession, obj_in: Dict[str, Any]) -> T:
        """Update a record."""
        for key, value in obj_in.items():
            setattr(self, key, value)
        self.updated_at = datetime.now()
        db.add(self)
        await db.commit()
        await db.refresh(self)
        return self

    async def delete(self: T, db: AsyncSession) -> None:
        """Delete a record."""
        await db.delete(self)
        await db.commit()
