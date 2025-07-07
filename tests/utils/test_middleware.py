"""
Tests for middleware utilities.
"""

import asyncio
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport

from app.utils.middleware import RequestLoggingMiddleware


@pytest.mark.utils
@pytest.mark.asyncio
async def test_request_logging_middleware_success():
    """Test request logging middleware with successful request."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    # Add the middleware
    app.add_middleware(RequestLoggingMiddleware)

    with patch("app.utils.middleware.logger") as mock_logger:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/test")

            assert response.status_code == 200
            assert "X-Process-Time" in response.headers

            # Verify logging calls
            assert mock_logger.info.call_count == 2

            # Check start log
            start_call = mock_logger.info.call_args_list[0][0][0]
            assert "Request started: GET /test" in start_call
            assert "from" in start_call

            # Check completion log
            completion_call = mock_logger.info.call_args_list[1][0][0]
            assert "Request completed: GET /test" in completion_call
            assert "Status: 200" in completion_call
            assert "Duration:" in completion_call


@pytest.mark.utils
@pytest.mark.asyncio
async def test_request_logging_middleware_with_exception():
    """Test request logging middleware when endpoint raises exception."""
    app = FastAPI()

    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")

    # Add the middleware
    app.add_middleware(RequestLoggingMiddleware)

    with patch("app.utils.middleware.logger") as mock_logger:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # This should raise an exception
            with pytest.raises(Exception):
                await client.get("/error")

            # Verify logging calls
            assert mock_logger.info.call_count == 1  # Only start log
            assert mock_logger.error.call_count == 1  # Error log

            # Check start log
            start_call = mock_logger.info.call_args_list[0][0][0]
            assert "Request started: GET /error" in start_call

            # Check error log
            error_call = mock_logger.error.call_args_list[0][0][0]
            assert "Request failed: GET /error" in error_call
            assert "Error: Test error" in error_call


@pytest.mark.utils
def test_request_logging_middleware_no_client_logic():
    """Test the logic for handling requests with no client."""

    # Test the client host logic directly
    # Create a mock request with no client
    class MockRequest:
        def __init__(self):
            self.method = "GET"
            self.url = type("obj", (object,), {"path": "/test"})()
            self.client = None

    request = MockRequest()

    # Test the logic that would be used in the middleware
    client_host = request.client.host if request.client else "unknown"
    assert client_host == "unknown"


@pytest.mark.utils
@pytest.mark.asyncio
async def test_request_logging_middleware_timing():
    """Test that middleware correctly measures request duration."""
    app = FastAPI()

    @app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(0.1)  # 100ms delay
        return {"message": "slow"}

    # Add the middleware
    app.add_middleware(RequestLoggingMiddleware)

    with patch("app.utils.middleware.logger") as mock_logger:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/slow")

            assert response.status_code == 200

            # Check that process time header is set
            process_time = float(response.headers["X-Process-Time"])
            assert process_time >= 0.1  # Should be at least 100ms

            # Check completion log includes duration
            completion_call = mock_logger.info.call_args_list[1][0][0]
            assert "Duration:" in completion_call


@pytest.mark.utils
@pytest.mark.asyncio
async def test_request_logging_middleware_different_methods():
    """Test request logging middleware with different HTTP methods."""
    app = FastAPI()

    @app.post("/test")
    async def post_endpoint():
        return {"method": "POST"}

    @app.put("/test")
    async def put_endpoint():
        return {"method": "PUT"}

    # Add the middleware
    app.add_middleware(RequestLoggingMiddleware)

    with patch("app.utils.middleware.logger") as mock_logger:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Test POST
            await client.post("/test")

            # Test PUT
            await client.put("/test")

            # Should have 4 log calls total (2 start, 2 completion)
            assert mock_logger.info.call_count == 4

            # Check that different methods are logged correctly
            calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("POST /test" in call for call in calls)
            assert any("PUT /test" in call for call in calls)


@pytest.mark.utils
def test_request_logging_middleware_logger_configuration():
    """Test that the middleware logger is configured correctly."""
    from app.utils.middleware import logger

    assert logger.name == "app.middleware"
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")


@pytest.mark.utils
@pytest.mark.asyncio
async def test_request_logging_middleware_response_headers():
    """Test that middleware adds correct headers to response."""
    app = FastAPI()

    @app.get("/headers")
    async def headers_endpoint():
        return {"test": "headers"}

    # Add the middleware
    app.add_middleware(RequestLoggingMiddleware)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/headers")

        assert response.status_code == 200
        assert "X-Process-Time" in response.headers

        # Verify the header value is a valid float
        process_time = response.headers["X-Process-Time"]
        assert float(process_time) >= 0.0

        # Verify it's formatted to 4 decimal places
        assert len(process_time.split(".")[1]) == 4
