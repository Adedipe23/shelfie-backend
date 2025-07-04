from datetime import datetime, timedelta, timezone

from jose import jwt

from app.core.password import get_password_hash, verify_password
from app.core.security import create_access_token
from app.core.settings import get_settings

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
