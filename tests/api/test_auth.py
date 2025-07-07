import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.models.user import User, UserRole

settings = get_settings()


@pytest.mark.asyncio
async def test_login_success(
    client: AsyncClient,
    test_user: User,
):
    """Test successful login."""
    login_data = {
        "username": test_user.email,
        "password": "password123",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_with_trailing_slash(
    client: AsyncClient,
    test_user: User,
):
    """Test login with trailing slash (Tauri compatibility)."""
    login_data = {
        "username": test_user.email,
        "password": "password123",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login/",
        data=login_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(
    client: AsyncClient,
    test_user: User,
):
    """Test login with invalid credentials."""
    login_data = {
        "username": test_user.email,
        "password": "wrongpassword",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(
    client: AsyncClient,
    test_user: User,  # This ensures tables are created
):
    """Test login with non-existent user."""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "password123",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_inactive_user(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test login with inactive user."""
    # Create inactive user
    user_data = {
        "email": "inactive@example.com",
        "password": "password123",
        "full_name": "Inactive User",
        "role": UserRole.CASHIER,
        "is_active": False,
    }
    user = await User.create(db, obj_in=user_data)

    login_data = {
        "username": user.email,
        "password": "password123",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    assert response.status_code == 403
    assert "Inactive user" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_missing_fields(
    client: AsyncClient,
):
    """Test login with missing fields."""
    # Missing password
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": "test@example.com"},
    )
    assert response.status_code == 422

    # Missing username
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"password": "password123"},
    )
    assert response.status_code == 422

    # Empty data
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_success(
    client: AsyncClient,
    db: AsyncSession,
):
    """Test successful user registration."""
    user_data = {
        "email": "newuser@example.com",
        "password": "newpassword123",
        "full_name": "New User",
        "role": "cashier",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json=user_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert data["role"] == user_data["role"]
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data  # Should not expose password


@pytest.mark.asyncio
async def test_register_duplicate_email(
    client: AsyncClient,
    test_user: User,
):
    """Test registration with duplicate email."""
    user_data = {
        "email": test_user.email,
        "password": "newpassword123",
        "full_name": "Another User",
        "role": "cashier",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json=user_data,
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email(
    client: AsyncClient,
):
    """Test registration with invalid email."""
    user_data = {
        "email": "invalid-email",
        "password": "newpassword123",
        "full_name": "New User",
        "role": "cashier",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json=user_data,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password(
    client: AsyncClient,
):
    """Test registration with weak password."""
    user_data = {
        "email": "newuser@example.com",
        "password": "123",  # Too short
        "full_name": "New User",
        "role": "cashier",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json=user_data,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_fields(
    client: AsyncClient,
):
    """Test registration with missing required fields."""
    # Missing email
    user_data = {
        "password": "newpassword123",
        "full_name": "New User",
        "role": "cashier",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json=user_data,
    )
    assert response.status_code == 422

    # Missing password
    user_data = {
        "email": "newuser@example.com",
        "full_name": "New User",
        "role": "cashier",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/register",
        json=user_data,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_me_success(
    client: AsyncClient,
    test_user: User,
):
    """Test get current user endpoint."""
    # Login first
    login_data = {
        "username": test_user.email,
        "password": "password123",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    token = response.json()["access_token"]

    # Test get me endpoint
    response = await client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    assert data["role"] == test_user.role
    assert data["is_active"] == test_user.is_active
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_get_me_without_token(
    client: AsyncClient,
):
    """Test get current user without authentication."""
    response = await client.get(f"{settings.API_V1_STR}/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(
    client: AsyncClient,
):
    """Test get current user with invalid token."""
    response = await client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_malformed_token(
    client: AsyncClient,
):
    """Test get current user with malformed token."""
    response = await client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": "InvalidFormat"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_expiration_flow(
    client: AsyncClient,
    test_user: User,
):
    """Test token-based authentication flow."""
    # Login and get token
    login_data = {
        "username": test_user.email,
        "password": "password123",
    }
    response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Use token to access protected endpoint
    response = await client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # Token should work multiple times
    response = await client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
