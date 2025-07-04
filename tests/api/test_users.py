import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.models.user import User, UserRole

settings = get_settings()


@pytest.mark.asyncio
async def test_read_users(
    client: AsyncClient,
    test_admin: User,
    test_user: User,
):
    """Test reading users."""
    # Login as admin
    login_data = {
        "username": test_admin.email,
        "password": "adminpass123",
    }
    login_response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    token = login_response.json()["access_token"]

    # Get all users
    response = await client.get(
        f"{settings.API_V1_STR}/users/",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least admin and test user

    # Check if test users are included
    user_ids = [user["id"] for user in data]
    assert test_admin.id in user_ids
    assert test_user.id in user_ids


@pytest.mark.asyncio
async def test_create_user(
    client: AsyncClient,
    test_admin: User,
    db: AsyncSession,
):
    """Test creating a user."""
    # Login as admin
    login_data = {
        "username": test_admin.email,
        "password": "adminpass123",
    }
    login_response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    token = login_response.json()["access_token"]

    # Create a new user
    user_data = {
        "email": "newuser@example.com",
        "password": "newpassword123",
        "full_name": "New User",
        "role": UserRole.CASHIER.value,
    }
    response = await client.post(
        f"{settings.API_V1_STR}/users/",
        headers={"Authorization": f"Bearer {token}"},
        json=user_data,
    )

    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert data["role"] == user_data["role"]

    # Try to create a user with the same email
    response = await client.post(
        f"{settings.API_V1_STR}/users/",
        headers={"Authorization": f"Bearer {token}"},
        json=user_data,
    )

    # Check response
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_read_user(
    client: AsyncClient,
    test_admin: User,
    test_user: User,
):
    """Test reading a specific user."""
    # Login as admin
    login_data = {
        "username": test_admin.email,
        "password": "adminpass123",
    }
    login_response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    admin_token = login_response.json()["access_token"]

    # Login as regular user
    login_data = {
        "username": test_user.email,
        "password": "password123",
    }
    login_response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    user_token = login_response.json()["access_token"]

    # Admin can read any user
    response = await client.get(
        f"{settings.API_V1_STR}/users/{test_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK

    # User can read themselves
    response = await client.get(
        f"{settings.API_V1_STR}/users/{test_user.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_200_OK

    # User cannot read admin (returns 404 instead of 403 for security reasons)
    response = await client.get(
        f"{settings.API_V1_STR}/users/{test_admin.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_user(
    client: AsyncClient,
    test_admin: User,
    test_user: User,
):
    """Test updating a user."""
    # Login as admin
    login_data = {
        "username": test_admin.email,
        "password": "adminpass123",
    }
    login_response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    admin_token = login_response.json()["access_token"]

    # Login as regular user
    login_data = {
        "username": test_user.email,
        "password": "password123",
    }
    login_response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    user_token = login_response.json()["access_token"]

    # Admin can update any user
    update_data = {
        "full_name": "Updated User Name",
    }
    response = await client.put(
        f"{settings.API_V1_STR}/users/{test_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == update_data["full_name"]

    # User can update themselves
    update_data = {
        "full_name": "Self Updated Name",
    }
    response = await client.put(
        f"{settings.API_V1_STR}/users/{test_user.id}",
        headers={"Authorization": f"Bearer {user_token}"},
        json=update_data,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == update_data["full_name"]

    # User cannot update admin (returns 404 instead of 403 for security reasons)
    update_data = {
        "full_name": "Hacked Admin Name",
    }
    response = await client.put(
        f"{settings.API_V1_STR}/users/{test_admin.id}",
        headers={"Authorization": f"Bearer {user_token}"},
        json=update_data,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_user(
    client: AsyncClient,
    test_admin: User,
    db: AsyncSession,
):
    """Test deleting a user."""
    # Create a user to delete
    user_to_delete = await User.create(
        db,
        obj_in={
            "email": "delete_me@example.com",
            "password": "password123",
            "full_name": "Delete Me",
            "role": UserRole.CASHIER.value,
        },
    )

    # Login as admin
    login_data = {
        "username": test_admin.email,
        "password": "adminpass123",
    }
    login_response = await client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    admin_token = login_response.json()["access_token"]

    # Admin can delete a user
    response = await client.delete(
        f"{settings.API_V1_STR}/users/{user_to_delete.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK

    # Verify user is deleted
    response = await client.get(
        f"{settings.API_V1_STR}/users/{user_to_delete.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Admin cannot delete themselves
    response = await client.delete(
        f"{settings.API_V1_STR}/users/{test_admin.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
