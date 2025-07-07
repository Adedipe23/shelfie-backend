"""
Health check endpoints for monitoring and deployment verification.
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict

import psutil
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.settings import get_settings

settings = get_settings()
router = APIRouter()


def get_utc_timestamp() -> str:
    """Get current UTC timestamp as ISO string for API responses."""
    return datetime.now(timezone.utc).isoformat()


@router.get("/")
async def basic_health():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": get_utc_timestamp(),
        "service": "ISMS API",
        "version": settings.VERSION,
    }


@router.get("/health")
async def health_check():
    """Basic health check with minimal information."""
    return {"status": "healthy", "timestamp": get_utc_timestamp()}


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Detailed health check with system and database information."""
    if not settings.HEALTH_CHECK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health check endpoint is disabled",
        )

    start_time = time.time()
    health_data = {
        "status": "healthy",
        "timestamp": get_utc_timestamp(),
        "service": {
            "name": "ISMS API",
            "version": settings.VERSION,
            "environment": settings.ENV_MODE,
        },
        "checks": {},
    }

    # Database health check
    try:
        db_start = time.time()
        await db.execute(text("SELECT 1"))
        db_time = (time.time() - db_start) * 1000

        # Check user table
        user_count = await db.execute(text("SELECT COUNT(*) FROM users"))
        user_total = user_count.scalar()

        health_data["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_time, 2),
            "connection": "active",
            "users_count": user_total,
        }
    except Exception as e:
        health_data["status"] = "unhealthy"
        health_data["checks"]["database"] = {"status": "unhealthy", "error": str(e)}

    # System health check
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        health_data["checks"]["system"] = {
            "status": "healthy",
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": round((disk.used / disk.total) * 100, 2),
            },
            "cpu_percent": psutil.cpu_percent(interval=1),
        }
    except Exception as e:
        health_data["checks"]["system"] = {"status": "degraded", "error": str(e)}

    # Performance metrics
    total_time = (time.time() - start_time) * 1000
    health_data["performance"] = {"total_response_time_ms": round(total_time, 2)}

    return health_data


@router.get("/health/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Kubernetes-style readiness probe."""
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))

        return {"status": "ready", "timestamp": get_utc_timestamp()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}",
        )


@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes-style liveness probe."""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": time.time() - psutil.boot_time(),
    }


@router.get("/metrics")
async def metrics_endpoint(db: AsyncSession = Depends(get_db)):
    """Basic metrics endpoint for monitoring."""
    if not settings.METRICS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metrics endpoint is disabled"
        )

    try:
        # Database metrics
        user_count = await db.execute(text("SELECT COUNT(*) FROM users"))
        total_users = user_count.scalar()

        # System metrics
        memory = psutil.virtual_memory()

        return {
            "timestamp": get_utc_timestamp(),
            "metrics": {
                "users_total": total_users,
                "memory_usage_percent": memory.percent,
                "cpu_usage_percent": psutil.cpu_percent(interval=1),
                "disk_usage_percent": psutil.disk_usage("/").percent,
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect metrics: {str(e)}",
        )
