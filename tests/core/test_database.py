import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User


@pytest.mark.asyncio
async def test_get_db():
    """Test the get_db dependency."""
    from sqlmodel import SQLModel

    from app.core.database import engine

    # Create tables first
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Get a database session
    db_gen = get_db()
    db = await anext(db_gen)

    # Check if it's an AsyncSession
    assert isinstance(db, AsyncSession)

    # Test a simple query
    user_count = await db.execute(text("SELECT COUNT(*) FROM users"))
    count = user_count.scalar()
    assert isinstance(count, int)

    # Clean up
    try:
        await db_gen.aclose()
    except Exception:
        pass

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.mark.asyncio
async def test_db_transaction_commit(db: AsyncSession):
    """Test database transaction commit."""
    # Create a test user
    test_email = "db_test_commit@example.com"
    user = User(
        email=test_email,
        hashed_password="hashed_password",
        full_name="DB Test User",
        role="cashier",
    )

    # Add to session and commit
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Check if user was created
    result = await db.execute(
        text("SELECT * FROM users WHERE email = :email"), {"email": test_email}
    )
    db_user = result.fetchone()
    assert db_user is not None
    assert db_user.email == test_email


@pytest.mark.asyncio
async def test_db_transaction_rollback(db: AsyncSession):
    """Test database transaction rollback."""
    # Create a test user
    test_email = "db_test_rollback@example.com"
    user = User(
        email=test_email,
        hashed_password="hashed_password",
        full_name="DB Test User",
        role="cashier",
    )

    # Add to session
    db.add(user)

    # Rollback
    await db.rollback()

    # Check if user was not created
    result = await db.execute(
        text("SELECT * FROM users WHERE email = :email"), {"email": test_email}
    )
    db_user = result.fetchone()
    assert db_user is None
