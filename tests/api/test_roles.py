import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.permissions import PermissionRegistry
from app.core.settings import get_settings
from app.models.user import User

settings = get_settings()


@pytest.mark.asyncio
async def test_get_all_roles(
    client: AsyncClient,
    test_admin: User,
):
    """Test getting all roles."""
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

    # Get all roles
    response = await client.get(
        f"{settings.API_V1_STR}/roles/",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "admin" in data
    assert "manager" in data
    assert "cashier" in data


@pytest.mark.asyncio
async def test_get_all_permissions(
    client: AsyncClient,
    test_admin: User,
):
    """Test getting all permissions."""
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

    # Get all permissions
    response = await client.get(
        f"{settings.API_V1_STR}/roles/permissions",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check response
    assert response.status_code == status.HTTP_200_OK
    permissions = response.json()
    assert isinstance(permissions, list)
    assert len(permissions) > 0


@pytest.mark.asyncio
async def test_get_role_permissions(
    client: AsyncClient,
    test_admin: User,
):
    """Test getting permissions for a specific role."""
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

    # Get permissions for admin role
    response = await client.get(
        f"{settings.API_V1_STR}/roles/admin/permissions",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check response
    assert response.status_code == status.HTTP_200_OK
    permissions = response.json()
    assert isinstance(permissions, list)
    assert len(permissions) > 0

    # Get permissions for non-existent role
    response = await client.get(
        f"{settings.API_V1_STR}/roles/non_existent_role/permissions",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Check response
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_create_custom_role(
    client: AsyncClient,
    test_admin: User,
):
    """Test creating a custom role."""
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

    # Register test permissions
    test_perm = "test:api_create"
    PermissionRegistry.register_permission(test_perm)

    # Create a custom role
    role_name = "test_api_role"
    response = await client.post(
        f"{settings.API_V1_STR}/roles/custom",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "role_name": role_name,
            "permissions": [test_perm],
        },
    )

    # Check response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == role_name
    assert test_perm in data["permissions"]

    # Try to create a role with the same name
    response = await client.post(
        f"{settings.API_V1_STR}/roles/custom",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "role_name": role_name,
            "permissions": [test_perm],
        },
    )

    # Check response
    assert response.status_code == status.HTTP_400_BAD_REQUEST
