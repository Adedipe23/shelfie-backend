import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health
from app.api.v1.router import api_router
from app.core.database import create_db_and_tables
from app.core.logging import setup_logging
from app.core.settings import get_settings
from app.utils.middleware import RequestLoggingMiddleware
from app.utils.security_middleware import (
    CompressionMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)

# Set up logging
setup_logging()
logger = logging.getLogger("app")

# Get application settings
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):  # noqa: ARG001
    """
    FastAPI lifespan event handler.

    This runs on application startup and shutdown.
    """
    # Startup
    logger.info("Starting application")
    await create_db_and_tables()
    logger.info("Database tables created")

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
)

# Add security middleware (order matters - add before CORS!)
if settings.ENV_MODE == "production":
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=settings.RATE_LIMIT_REQUESTS,
        window_size=settings.RATE_LIMIT_WINDOW,
    )

    # Compression
    app.add_middleware(CompressionMiddleware)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
else:
    # In development mode without explicit CORS origins, allow all origins
    if settings.ENV_MODE == "development":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,  # Can't use credentials with allow_origins=["*"]
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=["*"],
            expose_headers=["*"],
        )

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include health check router (before API router for priority)
app.include_router(health.router, tags=["health"])

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint for health checks."""
    return {
        "status": "online",
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENV_MODE,
    }
