import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_user_creation(db: AsyncSession):
    """Test creating a user."""
    user_data = {
        "email": "test@example.com",
        "password": "password123",
        "full_name": "Test User",
        "role": UserRole.CASHIER,
    }

    user = await User.create(db, obj_in=user_data)

    assert user.id is not None
    assert user.email == user_data["email"]
    assert user.full_name == user_data["full_name"]
    assert user.role == UserRole.CASHIER.value
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.hashed_password != user_data["password"]  # Should be hashed


@pytest.mark.asyncio
async def test_user_creation_with_enum_role(db: AsyncSession):
    """Test creating a user with enum role."""
    user_data = {
        "email": "admin@example.com",
        "password": "adminpass123",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
        "is_superuser": True,
    }

    user = await User.create(db, obj_in=user_data)

    assert user.role == UserRole.ADMIN.value
    assert user.is_superuser is True


@pytest.mark.asyncio
async def test_user_creation_with_string_role(db: AsyncSession):
    """Test creating a user with string role."""
    user_data = {
        "email": "manager@example.com",
        "password": "managerpass123",
        "full_name": "Manager User",
        "role": "manager",
    }

    user = await User.create(db, obj_in=user_data)

    assert user.role == "manager"


@pytest.mark.asyncio
async def test_user_creation_custom_role(db: AsyncSession):
    """Test creating a user with custom role."""
    user_data = {
        "email": "custom@example.com",
        "password": "custompass123",
        "full_name": "Custom User",
        "role": "custom_role",
    }

    user = await User.create(db, obj_in=user_data)

    assert user.role == "custom_role"


@pytest.mark.asyncio
async def test_get_user_by_email(db: AsyncSession):
    """Test getting a user by email."""
    user_data = {
        "email": "findme@example.com",
        "password": "password123",
        "full_name": "Find Me User",
        "role": UserRole.CASHIER,
    }

    created_user = await User.create(db, obj_in=user_data)

    # Find the user
    found_user = await User.get_by_email(db, email="findme@example.com")

    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == created_user.email


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(db: AsyncSession):
    """Test getting a non-existent user by email."""
    user = await User.get_by_email(db, email="nonexistent@example.com")
    assert user is None


@pytest.mark.asyncio
async def test_verify_password_correct(db: AsyncSession):
    """Test password verification with correct password."""
    user_data = {
        "email": "password@example.com",
        "password": "correctpassword",
        "full_name": "Password User",
        "role": UserRole.CASHIER,
    }

    user = await User.create(db, obj_in=user_data)

    assert user.verify_password("correctpassword") is True


@pytest.mark.asyncio
async def test_verify_password_incorrect(db: AsyncSession):
    """Test password verification with incorrect password."""
    user_data = {
        "email": "password2@example.com",
        "password": "correctpassword",
        "full_name": "Password User 2",
        "role": UserRole.CASHIER,
    }

    user = await User.create(db, obj_in=user_data)

    assert user.verify_password("wrongpassword") is False


@pytest.mark.asyncio
async def test_update_password(db: AsyncSession):
    """Test updating user password."""
    user_data = {
        "email": "updatepass@example.com",
        "password": "oldpassword",
        "full_name": "Update Password User",
        "role": UserRole.CASHIER,
    }

    user = await User.create(db, obj_in=user_data)
    old_hash = user.hashed_password

    # Update password
    await user.update_password(db, "newpassword")

    # Verify old password doesn't work
    assert user.verify_password("oldpassword") is False

    # Verify new password works
    assert user.verify_password("newpassword") is True

    # Verify hash changed
    assert user.hashed_password != old_hash


@pytest.mark.asyncio
async def test_has_standard_role(db: AsyncSession):
    """Test checking if user has standard role."""
    user_data = {
        "email": "role@example.com",
        "password": "password123",
        "full_name": "Role User",
        "role": UserRole.MANAGER,
    }

    user = await User.create(db, obj_in=user_data)

    assert user.has_standard_role(UserRole.MANAGER) is True
    assert user.has_standard_role(UserRole.ADMIN) is False
    assert user.has_standard_role(UserRole.CASHIER) is False


@pytest.mark.asyncio
async def test_has_role_with_enum(db: AsyncSession):
    """Test checking if user has role using enum."""
    user_data = {
        "email": "role2@example.com",
        "password": "password123",
        "full_name": "Role User 2",
        "role": UserRole.ADMIN,
    }

    user = await User.create(db, obj_in=user_data)

    assert user.has_role(UserRole.ADMIN) is True
    assert user.has_role(UserRole.MANAGER) is False


@pytest.mark.asyncio
async def test_has_role_with_string(db: AsyncSession):
    """Test checking if user has role using string."""
    user_data = {
        "email": "role3@example.com",
        "password": "password123",
        "full_name": "Role User 3",
        "role": "custom_role",
    }

    user = await User.create(db, obj_in=user_data)

    assert user.has_role("custom_role") is True
    assert user.has_role("other_role") is False
    assert user.has_role(UserRole.ADMIN) is False


@pytest.mark.asyncio
async def test_user_defaults(db: AsyncSession):
    """Test user creation with default values."""
    user_data = {
        "email": "defaults@example.com",
        "password": "password123",
        "full_name": "Defaults User",
        # No role specified, should default to CASHIER
    }

    user = await User.create(db, obj_in=user_data)

    assert user.role == UserRole.CASHIER.value
    assert user.is_active is True
    assert user.is_superuser is False


@pytest.mark.asyncio
async def test_user_inactive_creation(db: AsyncSession):
    """Test creating an inactive user."""
    user_data = {
        "email": "inactive@example.com",
        "password": "password123",
        "full_name": "Inactive User",
        "role": UserRole.CASHIER,
        "is_active": False,
    }

    user = await User.create(db, obj_in=user_data)

    assert user.is_active is False


@pytest.mark.asyncio
async def test_user_superuser_creation(db: AsyncSession):
    """Test creating a superuser."""
    user_data = {
        "email": "super@example.com",
        "password": "superpass123",
        "full_name": "Super User",
        "role": UserRole.ADMIN,
        "is_superuser": True,
    }

    user = await User.create(db, obj_in=user_data)

    assert user.is_superuser is True


@pytest.mark.asyncio
async def test_user_email_uniqueness(db: AsyncSession):
    """Test that user emails must be unique."""
    user_data = {
        "email": "unique@example.com",
        "password": "password123",
        "full_name": "First User",
        "role": UserRole.CASHIER,
    }

    # Create first user
    await User.create(db, obj_in=user_data)

    # Try to create second user with same email
    user_data2 = {
        "email": "unique@example.com",  # Same email
        "password": "password456",
        "full_name": "Second User",
        "role": UserRole.MANAGER,
    }

    with pytest.raises(Exception):  # Should raise integrity error
        await User.create(db, obj_in=user_data2)


@pytest.mark.asyncio
async def test_user_password_hashing(db: AsyncSession):
    """Test that passwords are properly hashed."""
    password = "plaintextpassword"
    user_data = {
        "email": "hash@example.com",
        "password": password,
        "full_name": "Hash User",
        "role": UserRole.CASHIER,
    }

    user = await User.create(db, obj_in=user_data)

    # Password should be hashed, not stored as plaintext
    assert user.hashed_password != password
    assert len(user.hashed_password) > len(password)
    assert user.hashed_password.startswith("$")  # bcrypt hash format


@pytest.mark.asyncio
async def test_user_role_enum_values():
    """Test UserRole enum values."""
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.MANAGER.value == "manager"
    assert UserRole.CASHIER.value == "cashier"

    # Test enum iteration
    roles = list(UserRole)
    assert len(roles) == 3
    assert UserRole.ADMIN in roles
    assert UserRole.MANAGER in roles
    assert UserRole.CASHIER in roles
