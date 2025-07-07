import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("app.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request information."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and log information."""
        start_time = time.time()

        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        logger.info(f"Request started: {method} {path} from {client_host}")

        try:
            response = await call_next(request)

            process_time = time.time() - start_time

            logger.info(
                f"Request completed: {method} {path} - "
                f"Status: {response.status_code} - "
                f"Duration: {process_time:.4f}s"
            )

            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            return response

        except Exception as e:
            logger.error(f"Request failed: {method} {path} - Error: {str(e)}")
            raise
