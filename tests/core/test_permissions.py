from app.core.permissions import PermissionRegistry
from app.models.user import User, UserRole


def test_register_permission():
    """Test registering a permission."""
    # Register a test permission
    test_permission = "test:permission"
    PermissionRegistry.register_permission(
        test_permission, [UserRole.ADMIN, UserRole.MANAGER]
    )

    # Check if permission was registered
    assert test_permission in PermissionRegistry.get_all_permissions()

    # Check if permission was assigned to roles
    admin_permissions = PermissionRegistry.get_role_permissions(UserRole.ADMIN.value)
    manager_permissions = PermissionRegistry.get_role_permissions(
        UserRole.MANAGER.value
    )
    cashier_permissions = PermissionRegistry.get_role_permissions(
        UserRole.CASHIER.value
    )

    assert test_permission in admin_permissions
    assert test_permission in manager_permissions
    assert test_permission not in cashier_permissions


def test_register_custom_role():
    """Test registering a custom role."""
    # Register a test permission
    test_permission = "test:custom_role"
    PermissionRegistry.register_permission(test_permission)

    # Register a custom role
    custom_role = "custom_role"
    PermissionRegistry.register_custom_role(custom_role, {test_permission})

    # Check if role was registered with the permission
    role_permissions = PermissionRegistry.get_role_permissions(custom_role)
    assert test_permission in role_permissions


def test_has_permission():
    """Test checking if a user has a permission."""
    # Register a test permission
    test_permission = "test:has_permission"
    PermissionRegistry.register_permission(test_permission, [UserRole.MANAGER])

    # Create test users
    admin_user = User(
        id=1,
        email="admin@example.com",
        hashed_password="",
        full_name="Admin",
        role=UserRole.ADMIN.value,
        is_superuser=True,
    )
    manager_user = User(
        id=2,
        email="manager@example.com",
        hashed_password="",
        full_name="Manager",
        role=UserRole.MANAGER.value,
    )
    cashier_user = User(
        id=3,
        email="cashier@example.com",
        hashed_password="",
        full_name="Cashier",
        role=UserRole.CASHIER.value,
    )

    # Check permissions
    assert PermissionRegistry.has_permission(admin_user, test_permission)
    assert PermissionRegistry.has_permission(manager_user, test_permission)
    assert not PermissionRegistry.has_permission(cashier_user, test_permission)


def test_custom_role_permissions():
    """Test custom role permissions."""
    # Register test permissions
    perm1 = "test:custom1"
    perm2 = "test:custom2"
    PermissionRegistry.register_permission(perm1)
    PermissionRegistry.register_permission(perm2)

    # Register a custom role with one permission
    custom_role = "custom_test_role"
    PermissionRegistry.register_custom_role(custom_role, {perm1})

    # Create a user with the custom role
    custom_user = User(
        id=4,
        email="custom@example.com",
        hashed_password="",
        full_name="Custom",
        role=custom_role,
    )

    # Check permissions
    assert PermissionRegistry.has_permission(custom_user, perm1)
    assert not PermissionRegistry.has_permission(custom_user, perm2)

    # Update the role with both permissions
    PermissionRegistry.register_custom_role(custom_role, {perm1, perm2})

    # Check permissions again
    assert PermissionRegistry.has_permission(custom_user, perm1)
    assert PermissionRegistry.has_permission(custom_user, perm2)
