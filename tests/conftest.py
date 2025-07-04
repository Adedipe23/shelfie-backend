import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Set test environment
os.environ["ENV_MODE"] = "testing"
os.environ["SQLITE_DATABASE_URI"] = "sqlite+aiosqlite:///:memory:"

# Import app after setting environment variables
from app.core.database import get_db
from app.main import app as fastapi_app

# Import all models to ensure they're registered with SQLModel
from app.models import inventory, sales, user  # noqa: F401
from app.models.user import User, UserRole

# Create test database engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True,
)

# Create test session factory
test_async_session_factory = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database for each test.
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Create session
    async with test_async_session_factory() as session:
        yield session

    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
def app() -> FastAPI:
    """
    Create a FastAPI app for testing.
    """

    # Override the get_db dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_async_session_factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    return fastapi_app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an HTTP client for testing.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    """
    Create a test user.
    """
    user_data = {
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User",
        "role": UserRole.CASHIER,
    }
    user = await User.create(db, obj_in=user_data)
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db: AsyncSession) -> User:
    """
    Create a test admin user.
    """
    admin_data = {
        "email": "admin@example.com",
        "password": "adminpass123",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
        "is_superuser": True,
    }
    admin = await User.create(db, obj_in=admin_data)
    await db.refresh(admin)
    return admin
