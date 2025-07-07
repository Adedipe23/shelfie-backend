"""
Tests for security middleware.
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport

from app.core.settings import get_settings
from app.utils.security_middleware import (
    CompressionMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)

settings = get_settings()


@pytest.mark.core
@pytest.mark.asyncio
async def test_security_headers_middleware_directly():
    """Test SecurityHeadersMiddleware directly."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test with security headers enabled
        with (
            patch.object(settings, "SECURE_HEADERS", True),
            patch.object(settings, "HTTPS_ONLY", True),
        ):
            response = await client.get("/test")

            # Check security headers
            assert "X-Content-Type-Options" in response.headers
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert "X-Frame-Options" in response.headers
            assert response.headers["X-Frame-Options"] == "DENY"
            assert "X-XSS-Protection" in response.headers
            assert "Referrer-Policy" in response.headers
            assert "Permissions-Policy" in response.headers
            assert "Strict-Transport-Security" in response.headers
            assert "Content-Security-Policy" in response.headers


@pytest.mark.core
@pytest.mark.asyncio
async def test_rate_limiting_middleware_directly():
    """Test RateLimitMiddleware directly."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    # Add rate limiting middleware with very low limits for testing
    app.add_middleware(RateLimitMiddleware, requests_per_minute=2, window_size=60)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        with patch.object(settings, "RATE_LIMIT_ENABLED", True):
            # First request should succeed
            response1 = await client.get("/test")
            assert response1.status_code == 200
            assert "X-RateLimit-Limit" in response1.headers
            assert response1.headers["X-RateLimit-Limit"] == "2"

            # Second request should succeed
            response2 = await client.get("/test")
            assert response2.status_code == 200

            # Third request should be rate limited
            response3 = await client.get("/test")
            assert response3.status_code == 429
            assert "Rate limit exceeded" in response3.json()["detail"]


@pytest.mark.core
@pytest.mark.asyncio
async def test_compression_middleware_directly():
    """Test CompressionMiddleware directly."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    # Add compression middleware
    app.add_middleware(CompressionMiddleware)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test", headers={"Accept-Encoding": "gzip"})

        # Check if Vary header is set for JSON responses
        if "application/json" in response.headers.get("content-type", ""):
            assert "Vary" in response.headers
            assert response.headers["Vary"] == "Accept-Encoding"


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
async def test_rate_limiting_disabled():
    """Test that rate limiting is disabled when RATE_LIMIT_ENABLED is False."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware, requests_per_minute=1, window_size=60)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        with patch.object(settings, "RATE_LIMIT_ENABLED", False):
            # Multiple requests should all succeed without rate limiting
            for _ in range(5):
                response = await client.get("/test")
                assert response.status_code == 200
                # Should still have rate limit headers when middleware is active
                assert "X-RateLimit-Limit" in response.headers


@pytest.mark.core
@pytest.mark.asyncio
async def test_security_headers_disabled():
    """Test that security headers are not added when SECURE_HEADERS is False."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        with patch.object(settings, "SECURE_HEADERS", False):
            response = await client.get("/test")

            # Security headers should not be present
            assert "X-Content-Type-Options" not in response.headers
            assert "X-Frame-Options" not in response.headers
            assert "Strict-Transport-Security" not in response.headers


@pytest.mark.core
@pytest.mark.asyncio
async def test_rate_limit_health_endpoints_bypass():
    """Test that health endpoints bypass rate limiting."""
    app = FastAPI()

    @app.get("/")
    async def root():
        return {"status": "ok"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/api/v1/health")
    async def api_health():
        return {"status": "healthy"}

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    # Add rate limiting middleware with very low limits
    app.add_middleware(RateLimitMiddleware, requests_per_minute=1, window_size=60)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        with patch.object(settings, "RATE_LIMIT_ENABLED", True):
            # Health endpoints should bypass rate limiting
            for _ in range(3):
                response = await client.get("/")
                assert response.status_code == 200

                response = await client.get("/health")
                assert response.status_code == 200

                response = await client.get("/api/v1/health")
                assert response.status_code == 200

            # Regular endpoint should be rate limited after first request
            response1 = await client.get("/test")
            assert response1.status_code == 200

            response2 = await client.get("/test")
            assert response2.status_code == 429


@pytest.mark.core
def test_rate_limit_get_client_ip():
    """Test client IP extraction logic."""
    from app.utils.security_middleware import RateLimitMiddleware

    app = FastAPI()
    middleware = RateLimitMiddleware(app)

    # Mock request with X-Forwarded-For header
    class MockClient:
        host = "127.0.0.1"

    class MockRequest:
        def __init__(self, headers=None, client=None):
            self.headers = headers or {}
            self.client = client

    # Test X-Forwarded-For header
    request = MockRequest(headers={"X-Forwarded-For": "192.168.1.1, 10.0.0.1"})
    assert middleware.get_client_ip(request) == "192.168.1.1"

    # Test X-Real-IP header
    request = MockRequest(headers={"X-Real-IP": "192.168.1.2"})
    assert middleware.get_client_ip(request) == "192.168.1.2"

    # Test fallback to client.host
    request = MockRequest(client=MockClient())
    assert middleware.get_client_ip(request) == "127.0.0.1"

    # Test no client
    request = MockRequest()
    assert middleware.get_client_ip(request) == "unknown"


@pytest.mark.core
@pytest.mark.asyncio
async def test_compression_middleware_no_gzip():
    """Test compression middleware when gzip is not accepted."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    # Add compression middleware
    app.add_middleware(CompressionMiddleware)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Explicitly set Accept-Encoding to something that doesn't include gzip
        response = await client.get("/test", headers={"Accept-Encoding": "deflate"})

        # Vary header should not be set when gzip is not in accept-encoding
        assert "Vary" not in response.headers
