"""
Tests for health check endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings

settings = get_settings()


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_basic_health_check(client: AsyncClient):
    """Test basic health check endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "ISMS API"
    assert data["version"] == settings.VERSION


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_detailed_health_check(client: AsyncClient, db: AsyncSession):
    """Test detailed health check endpoint."""
    # Enable health checks for testing
    settings.HEALTH_CHECK_ENABLED = True

    response = await client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "service" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "system" in data["checks"]
    assert "performance" in data


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient, db: AsyncSession):
    """Test readiness probe endpoint."""
    response = await client.get("/health/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "timestamp" in data


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_liveness_check(client: AsyncClient):
    """Test liveness probe endpoint."""
    response = await client.get("/health/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert "uptime_seconds" in data


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient, db: AsyncSession):
    """Test metrics endpoint."""
    # Enable metrics for testing
    settings.METRICS_ENABLED = True

    response = await client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "metrics" in data
    assert "users_total" in data["metrics"]
    assert "memory_usage_percent" in data["metrics"]
    assert "cpu_usage_percent" in data["metrics"]
    assert "disk_usage_percent" in data["metrics"]


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check_disabled(client: AsyncClient):
    """Test health check when disabled."""
    # Disable health checks
    settings.HEALTH_CHECK_ENABLED = False

    response = await client.get("/health/detailed")
    assert response.status_code == 404
    data = response.json()
    assert "Health check endpoint is disabled" in data["detail"]


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.asyncio
async def test_metrics_disabled(client: AsyncClient):
    """Test metrics when disabled."""
    # Disable metrics
    settings.METRICS_ENABLED = False

    response = await client.get("/metrics")
    assert response.status_code == 404
    data = response.json()
    assert "Metrics endpoint is disabled" in data["detail"]
