import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import PermissionRegistry
from app.services.role_service import RoleService


@pytest.mark.asyncio
async def test_get_all_permissions():
    """Test getting all permissions."""
    # Register a test permission
    test_permission = "test:get_all"
    PermissionRegistry.register_permission(test_permission)

    # Get all permissions
    permissions = await RoleService.get_all_permissions()

    # Check if the test permission is included
    assert test_permission in permissions

    # Check if permissions are sorted
    assert permissions == sorted(permissions)


@pytest.mark.asyncio
async def test_get_all_roles():
    """Test getting all roles with their permissions."""
    # Register a test permission and assign to a role
    test_permission = "test:get_roles"
    PermissionRegistry.register_permission(test_permission)

    # Get all roles
    roles = await RoleService.get_all_roles()

    # Check if standard roles are included
    assert "admin" in roles
    assert "manager" in roles
    assert "cashier" in roles

    # Check if admin has the test permission
    assert test_permission in roles["admin"]


@pytest.mark.asyncio
async def test_get_role_permissions():
    """Test getting permissions for a specific role."""
    # Register a test permission and assign to a role
    test_permission = "test:get_role_permissions"
    PermissionRegistry.register_permission(test_permission)

    # Get permissions for admin role
    admin_permissions = await RoleService.get_role_permissions("admin")

    # Check if the test permission is included
    assert test_permission in admin_permissions

    # Check if permissions are sorted
    assert admin_permissions == sorted(admin_permissions)

    # Test getting permissions for non-existent role
    with pytest.raises(HTTPException):
        await RoleService.get_role_permissions("non_existent_role")


@pytest.mark.asyncio
async def test_create_custom_role():
    """Test creating a custom role."""
    # Register test permissions
    perm1 = "test:custom_create1"
    perm2 = "test:custom_create2"
    PermissionRegistry.register_permission(perm1)
    PermissionRegistry.register_permission(perm2)

    # Create a custom role
    role_name = "test_custom_role_create"
    role_data = await RoleService.create_custom_role(role_name, {perm1, perm2})

    # Check the returned data
    assert role_data["name"] == role_name
    assert perm1 in role_data["permissions"]
    assert perm2 in role_data["permissions"]

    # Check if the role was actually created
    role_permissions = PermissionRegistry.get_role_permissions(role_name)
    assert perm1 in role_permissions
    assert perm2 in role_permissions

    # Test creating a role with an existing name
    with pytest.raises(HTTPException):
        await RoleService.create_custom_role(role_name, {perm1})

    # Test creating a role with a standard role name
    with pytest.raises(HTTPException):
        await RoleService.create_custom_role("admin", {perm1})

    # Test creating a role with invalid permissions
    with pytest.raises(HTTPException):
        await RoleService.create_custom_role("another_role", {"invalid:permission"})


@pytest.mark.asyncio
async def test_update_custom_role():
    """Test updating a custom role."""
    # Register test permissions
    perm1 = "test:custom_update1"
    perm2 = "test:custom_update2"
    PermissionRegistry.register_permission(perm1)
    PermissionRegistry.register_permission(perm2)

    # Create a custom role
    role_name = "test_custom_role_update"
    await RoleService.create_custom_role(role_name, {perm1})

    # Update the role
    role_data = await RoleService.update_custom_role(role_name, {perm1, perm2})

    # Check the returned data
    assert role_data["name"] == role_name
    assert perm1 in role_data["permissions"]
    assert perm2 in role_data["permissions"]

    # Check if the role was actually updated
    role_permissions = PermissionRegistry.get_role_permissions(role_name)
    assert perm1 in role_permissions
    assert perm2 in role_permissions

    # Test updating a non-existent role
    with pytest.raises(HTTPException):
        await RoleService.update_custom_role("non_existent_role", {perm1})

    # Test updating a standard role
    with pytest.raises(HTTPException):
        await RoleService.update_custom_role("admin", {perm1})


@pytest.mark.asyncio
async def test_delete_custom_role(db: AsyncSession):
    """Test deleting a custom role."""
    # Register test permissions
    perm = "test:custom_delete"
    PermissionRegistry.register_permission(perm)

    # Create a custom role
    role_name = "test_custom_role_delete"
    await RoleService.create_custom_role(role_name, {perm})

    # Delete the role
    role_data = await RoleService.delete_custom_role(role_name, db)

    # Check the returned data
    assert role_data["name"] == role_name
    assert perm in role_data["permissions"]

    # Check if the role was actually deleted
    with pytest.raises(HTTPException):
        await RoleService.get_role_permissions(role_name)

    # Test deleting a non-existent role
    with pytest.raises(HTTPException):
        await RoleService.delete_custom_role("non_existent_role", db)

    # Test deleting a standard role
    with pytest.raises(HTTPException):
        await RoleService.delete_custom_role("admin", db)
