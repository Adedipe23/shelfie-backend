"""
Security middleware for production deployment.
Implements security headers, rate limiting, and other security measures.
"""

import time
from collections import defaultdict, deque
from typing import Dict

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.settings import get_settings

settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if settings.SECURE_HEADERS:
            # Security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=()"
            )

            if settings.HTTPS_ONLY:
                response.headers["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains"
                )

            # Content Security Policy - Allow Swagger UI CDN resources
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net blob:; "
                "worker-src 'self' blob:; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "style-src-elem 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.isms.helevon.org https://isms-ismsbackend-jc2q7s-1afe24-93-127-213-33.traefik.me tauri://localhost; "
                "frame-ancestors 'none';"
            )
            response.headers["Content-Security-Policy"] = csp

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window algorithm."""

    def __init__(self, app, requests_per_minute: int = 100, window_size: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = window_size
        self.clients: Dict[str, deque] = defaultdict(deque)

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers (common in reverse proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"

    def is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        if not settings.RATE_LIMIT_ENABLED:
            return False

        now = time.time()
        client_requests = self.clients[client_ip]

        # Remove old requests outside the window
        while client_requests and client_requests[0] <= now - self.window_size:
            client_requests.popleft()

        # Check if limit exceeded
        if len(client_requests) >= self.requests_per_minute:
            return True

        # Add current request
        client_requests.append(now)
        return False

    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_client_ip(request)

        # Skip rate limiting for health checks
        if request.url.path in ["/", "/health", "/api/v1/health"]:
            return await call_next(request)

        if self.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                },
                headers={
                    "Retry-After": str(self.window_size),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Window": str(self.window_size),
                },
            )

        response = await call_next(request)

        # Add rate limit headers to response
        client_requests = self.clients[client_ip]
        remaining = max(0, self.requests_per_minute - len(client_requests))

        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.window_size)

        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Simple compression middleware for JSON responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add compression hint for reverse proxy
        if "application/json" in response.headers.get(
            "content-type", ""
        ) and "gzip" in request.headers.get("accept-encoding", ""):
            response.headers["Vary"] = "Accept-Encoding"

        return response
