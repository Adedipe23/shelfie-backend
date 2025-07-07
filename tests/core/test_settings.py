import os
from unittest.mock import patch

import pytest

from app.core.settings import Settings, get_settings


def test_settings_defaults():
    """Test default settings values."""
    # Override environment variables for this test
    with patch.dict(os.environ, {"ENV_MODE": "development"}):
        settings = Settings()

        # Check API settings
        assert settings.API_V1_STR == "/api/v1"
        assert "Integrated Supermarket Management System" in settings.PROJECT_NAME
        assert settings.VERSION is not None

        # Check database settings
        assert settings.ENV_MODE == "development"
        assert "sqlite" in settings.SQLITE_DATABASE_URI

        # Check security settings
        assert settings.SECRET_KEY is not None
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0


def test_settings_from_env():
    """Test loading settings from environment variables."""
    # Set environment variables
    env_vars = {
        "PROJECT_NAME": "Test Project",
        "VERSION": "1.2.3",
        "ENV_MODE": "testing",
        "SECRET_KEY": "test_secret_key",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "120",
        "LOG_LEVEL": "DEBUG",
    }

    with patch.dict(os.environ, env_vars):
        settings = Settings()

        # Check if environment variables were loaded
        assert settings.PROJECT_NAME == "Test Project"
        assert settings.VERSION == "1.2.3"
        assert settings.ENV_MODE == "testing"
        assert settings.SECRET_KEY == "test_secret_key"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 120
        assert settings.LOG_LEVEL == "DEBUG"


def test_database_uri_validator():
    """Test database URI validator."""
    # Test development mode (SQLite)
    settings = Settings(ENV_MODE="development")
    assert "sqlite" in settings.DATABASE_URI

    # Test production mode with PostgreSQL settings
    settings = Settings(
        ENV_MODE="production",
        POSTGRES_SERVER="localhost",
        POSTGRES_USER="postgres",
        POSTGRES_PASSWORD="password",
        POSTGRES_DB="isms",
    )
    assert "postgresql" in settings.DATABASE_URI

    # Test production mode without PostgreSQL settings
    with pytest.raises(ValueError):
        Settings(ENV_MODE="production")


def test_cors_origins_validator():
    """Test CORS origins validator."""
    # Test with string
    settings = Settings(BACKEND_CORS_ORIGINS="http://localhost,http://example.com")
    assert len(settings.BACKEND_CORS_ORIGINS) == 2
    # In Pydantic v2, AnyHttpUrl objects are returned instead of strings
    assert any(
        str(url).startswith("http://localhost") for url in settings.BACKEND_CORS_ORIGINS
    )
    assert any(
        str(url).startswith("http://example.com")
        for url in settings.BACKEND_CORS_ORIGINS
    )

    # Test with list
    settings = Settings(BACKEND_CORS_ORIGINS=["http://localhost", "http://example.com"])
    assert len(settings.BACKEND_CORS_ORIGINS) == 2
    assert any(
        str(url).startswith("http://localhost") for url in settings.BACKEND_CORS_ORIGINS
    )
    assert any(
        str(url).startswith("http://example.com")
        for url in settings.BACKEND_CORS_ORIGINS
    )


def test_get_settings():
    """Test get_settings function."""
    # Call get_settings multiple times
    settings1 = get_settings()
    settings2 = get_settings()

    # Check if the same instance is returned (lru_cache)
    assert settings1 is settings2
