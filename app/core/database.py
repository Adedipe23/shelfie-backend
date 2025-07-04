import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.settings import get_settings

settings = get_settings()

# Create async engine based on settings
engine_kwargs = {
    "echo": settings.ENV_MODE == "development",
    "future": True,
}

# Add connection pool settings for PostgreSQL in production
if settings.ENV_MODE == "production" and "postgresql" in (settings.DATABASE_URI or ""):
    engine_kwargs.update(
        {
            "pool_size": settings.POOL_SIZE,
            "max_overflow": settings.MAX_OVERFLOW,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # Recycle connections every hour
        }
    )

engine = create_async_engine(
    settings.DATABASE_URI or settings.SQLITE_DATABASE_URI, **engine_kwargs
)

# Create async session factory
async_session_factory = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_db_and_tables() -> None:
    """Create database tables on application startup."""
    logger = logging.getLogger("app.database")

    async with engine.begin() as conn:
        try:
            # Create all tables and types
            await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            error_msg = str(e)

            # Handle PostgreSQL enum type conflicts gracefully
            if (
                "duplicate key value violates unique constraint" in error_msg
                and "pg_type_typname_nsp_index" in error_msg
            ):
                logger.warning(
                    "PostgreSQL enum types already exist, this is normal for existing databases"
                )
                logger.info("Database initialization completed (enums already existed)")
            else:
                logger.error(f"Failed to create database tables: {e}")
                # Re-raise the exception if it's not an enum conflict
                raise
