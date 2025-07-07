from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.password import get_password_hash, verify_password
from app.core.security import (
    create_access_token,
    get_current_active_superuser,
    get_current_user,
)
from app.core.settings import get_settings
from app.models.user import User, UserRole

settings = get_settings()


def test_password_hashing():
    """Test password hashing and verification."""
    # Hash a password
    password = "testpassword123"
    hashed = get_password_hash(password)

    # Verify the password
    assert verify_password(password, hashed)

    # Verify with wrong password
    assert not verify_password("wrongpassword", hashed)

    # Verify that hashing the same password twice gives different hashes
    hashed2 = get_password_hash(password)
    assert hashed != hashed2


def test_create_access_token():
    """Test creating JWT access tokens."""
    # Create a token
    user_id = 123
    token = create_access_token(user_id)

    # Decode the token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

    # Check payload
    assert payload["sub"] == str(user_id)
    assert "exp" in payload

    # Check expiration
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    assert exp > now

    # Default expiration should be settings.ACCESS_TOKEN_EXPIRE_MINUTES
    # Just check that it's a reasonable value, not the exact value
    assert (exp - now) < timedelta(days=10)  # Should be less than 10 days

    # Test with custom expiration
    custom_expires = timedelta(minutes=30)
    token = create_access_token(user_id, expires_delta=custom_expires)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    # Update now for the second check
    now = datetime.now(timezone.utc)
    # Allow for a bit of execution time between token creation and now
    assert (exp - now) < timedelta(minutes=31)
    assert (exp - now) > timedelta(minutes=25)


@pytest.mark.asyncio
async def test_get_current_user_valid_token(db: AsyncSession):
    """Test get_current_user with valid token."""
    # Create a test user
    test_user = User(
        email="test_security@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Security User",
        role=UserRole.CASHIER.value,
        is_active=True,
    )

    db.add(test_user)
    await db.commit()
    await db.refresh(test_user)

    # Create a valid token
    token = create_access_token(test_user.id)

    # Test get_current_user
    current_user = await get_current_user(db, token)
    assert current_user is not None
    assert current_user.id == test_user.id
    assert current_user.email == test_user.email


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db: AsyncSession):
    """Test get_current_user with invalid token."""
    # Test with invalid token
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(db, "invalid_token")

    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_expired_token(db: AsyncSession):
    """Test get_current_user with expired token."""
    # Create a test user
    test_user = User(
        email="test_expired@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Expired User",
        role=UserRole.CASHIER.value,
        is_active=True,
    )

    db.add(test_user)
    await db.commit()
    await db.refresh(test_user)

    # Create an expired token (negative expiration)
    expired_token = create_access_token(
        test_user.id, expires_delta=timedelta(seconds=-1)
    )

    # Test with expired token
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(db, expired_token)

    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_nonexistent_user(db: AsyncSession):
    """Test get_current_user with token for non-existent user."""
    # Create a token for a non-existent user
    token = create_access_token(99999)  # Non-existent user ID

    # Test with token for non-existent user
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(db, token)

    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_inactive_user(db: AsyncSession):
    """Test get_current_user with inactive user."""
    # Create an inactive test user
    test_user = User(
        email="test_inactive@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test Inactive User",
        role=UserRole.CASHIER.value,
        is_active=False,  # Inactive user
    )

    db.add(test_user)
    await db.commit()
    await db.refresh(test_user)

    # Create a valid token
    token = create_access_token(test_user.id)

    # Test with inactive user
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(db, token)

    assert exc_info.value.status_code == 403
    assert "Inactive user" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_active_superuser_valid(db: AsyncSession):
    """Test get_current_active_superuser with valid superuser."""
    # Create a superuser
    superuser = User(
        email="superuser@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Super User",
        role=UserRole.ADMIN.value,
        is_active=True,
        is_superuser=True,
    )

    db.add(superuser)
    await db.commit()
    await db.refresh(superuser)

    # Test get_current_active_superuser
    result = await get_current_active_superuser(superuser)
    assert result is not None
    assert result.id == superuser.id
    assert result.is_superuser is True


@pytest.mark.asyncio
async def test_get_current_active_superuser_not_superuser(db: AsyncSession):
    """Test get_current_active_superuser with regular user."""
    # Create a regular user
    regular_user = User(
        email="regular@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Regular User",
        role=UserRole.CASHIER.value,
        is_active=True,
        is_superuser=False,
    )

    db.add(regular_user)
    await db.commit()
    await db.refresh(regular_user)

    # Test with regular user
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_superuser(regular_user)

    assert exc_info.value.status_code == 403
    assert "Not enough permissions" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_malformed_token(db: AsyncSession):
    """Test get_current_user with malformed JWT token."""
    # Create a malformed token (not proper JWT format)
    malformed_token = "not.a.valid.jwt.token"

    # Test with malformed token
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(db, malformed_token)

    assert exc_info.value.status_code == 401
    assert "Could not validate credentials" in exc_info.value.detail


def test_create_access_token_with_string_subject():
    """Test creating access token with string subject."""
    # Test with string subject
    subject = "user@example.com"
    token = create_access_token(subject)

    # Decode and verify
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == subject


def test_create_access_token_with_zero_expiration():
    """Test creating access token with zero expiration delta."""
    user_id = 123

    # Create token with zero expiration delta
    # Note: timedelta(0) is falsy, so the function will use default expiration
    token = create_access_token(user_id, expires_delta=timedelta(0))

    # Decode and verify the expiration
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)

    # Since timedelta(0) is falsy, it should use the default expiration time
    # which is settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expected_duration = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # The expiration should be close to now + default duration
    assert (exp - now) < expected_duration + timedelta(minutes=1)  # Allow some margin
    assert (exp - now) > expected_duration - timedelta(minutes=1)  # Allow some margin
