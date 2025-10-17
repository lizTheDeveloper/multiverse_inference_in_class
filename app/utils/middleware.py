"""Custom middleware for the FastAPI application.

This module contains middleware for:
- Request body size limiting
- Request ID generation and tracking
- Error handling improvements
"""

import uuid
import time
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.utils.logger import get_logger
from app.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size.

    This prevents memory exhaustion from very large request bodies.
    """

    def __init__(self, app: ASGIApp, max_size: int = 1_048_576):
        """Initialize the middleware.

        Args:
            app: The ASGI application
            max_size: Maximum request body size in bytes (default: 1MB)
        """
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and enforce size limits.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint

        Returns:
            Response from the endpoint or error response
        """
        # Check Content-Length header if present
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > self.max_size:
            logger.warning(
                f"Request body too large: {content_length} bytes "
                f"(max: {self.max_size} bytes) from {request.client.host}"
            )
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": {
                        "message": f"Request body too large. Maximum size is {self.max_size} bytes.",
                        "type": "request_too_large",
                        "code": "413"
                    }
                }
            )

        response = await call_next(request)
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and track request IDs for logging correlation.

    Adds a unique request ID to each request for tracing through logs.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add request ID.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint

        Returns:
            Response with X-Request-ID header
        """
        # Generate or use existing request ID
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        # Store request ID in request state for use in endpoints
        request.state.request_id = request_id

        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Log request completion
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration_ms}ms",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "unknown"
            }
        )

        return response
