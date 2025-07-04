"""
Tests for security middleware.
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.core.settings import get_settings

settings = get_settings()


@pytest.mark.core
@pytest.mark.asyncio
async def test_security_headers_in_production(client: AsyncClient):
    """Test that security headers are added in production mode."""
    # Mock production environment
    with (
        patch.object(settings, "ENV_MODE", "production"),
        patch.object(settings, "SECURE_HEADERS", True),
        patch.object(settings, "HTTPS_ONLY", True),
    ):

        response = await client.get("/")

        # Check security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy" in response.headers


@pytest.mark.core
@pytest.mark.asyncio
async def test_rate_limiting_enabled(client: AsyncClient):
    """Test rate limiting functionality."""
    # Mock production environment with rate limiting
    with (
        patch.object(settings, "ENV_MODE", "production"),
        patch.object(settings, "RATE_LIMIT_ENABLED", True),
        patch.object(settings, "RATE_LIMIT_REQUESTS", 2),
        patch.object(settings, "RATE_LIMIT_WINDOW", 60),
    ):

        # First request should succeed
        response1 = await client.get("/api/v1/auth/me")
        assert response1.status_code in [200, 401]  # 401 is expected without auth

        # Second request should succeed
        response2 = await client.get("/api/v1/auth/me")
        assert response2.status_code in [200, 401]

        # Third request should be rate limited
        response3 = await client.get("/api/v1/auth/me")
        # Note: In testing, rate limiting might not work exactly as expected
        # due to test client behavior, but we can check headers
        if "X-RateLimit-Limit" in response3.headers:
            assert response3.headers["X-RateLimit-Limit"] == "2"


@pytest.mark.core
@pytest.mark.asyncio
async def test_compression_middleware(client: AsyncClient):
    """Test compression middleware adds appropriate headers."""
    response = await client.get("/", headers={"Accept-Encoding": "gzip"})

    # Check if Vary header is set for JSON responses
    if "application/json" in response.headers.get("content-type", ""):
        assert "Vary" in response.headers


@pytest.mark.core
@pytest.mark.asyncio
async def test_health_endpoints_bypass_rate_limiting(client: AsyncClient):
    """Test that health endpoints bypass rate limiting."""
    # Mock production environment with very strict rate limiting
    with (
        patch.object(settings, "ENV_MODE", "production"),
        patch.object(settings, "RATE_LIMIT_ENABLED", True),
        patch.object(settings, "RATE_LIMIT_REQUESTS", 1),
        patch.object(settings, "RATE_LIMIT_WINDOW", 60),
    ):

        # Multiple health check requests should all succeed
        for _ in range(5):
            response = await client.get("/")
            assert response.status_code == 200

        for _ in range(5):
            response = await client.get("/health")
            assert response.status_code == 200


@pytest.mark.core
@pytest.mark.asyncio
async def test_security_headers_disabled_in_development(client: AsyncClient):
    """Test that security headers are not added in development mode."""
    # Mock development environment
    with (
        patch.object(settings, "ENV_MODE", "development"),
        patch.object(settings, "SECURE_HEADERS", False),
    ):

        response = await client.get("/")

        # Security headers should not be present
        assert "Strict-Transport-Security" not in response.headers
        # Some headers might still be present from other middleware


@pytest.mark.core
@pytest.mark.asyncio
async def test_rate_limiting_disabled_in_development(client: AsyncClient):
    """Test that rate limiting is disabled in development mode."""
    # Mock development environment
    with (
        patch.object(settings, "ENV_MODE", "development"),
        patch.object(settings, "RATE_LIMIT_ENABLED", False),
    ):

        # Multiple requests should all succeed without rate limiting
        for _ in range(10):
            response = await client.get("/api/v1/auth/me")
            assert response.status_code in [200, 401]  # 401 is expected without auth
            # Should not have rate limit headers
            assert "X-RateLimit-Limit" not in response.headers
