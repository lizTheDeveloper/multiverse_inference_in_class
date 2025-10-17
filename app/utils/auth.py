"""Authentication utilities for the inference gateway.

This module provides functions and dependencies for API key authentication.
"""

from typing import Annotated
from fastapi import Header, HTTPException, status

from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def verify_admin_api_key(
    x_api_key: Annotated[str, Header(description="Admin API key")]
) -> str:
    """Dependency to verify admin API key from X-API-Key header.
    
    This function is used as a FastAPI dependency to protect admin endpoints.
    It checks that the X-API-Key header matches the configured admin API key.
    
    Args:
        x_api_key: API key from X-API-Key header
    
    Returns:
        The validated API key
    
    Raises:
        HTTPException: If API key is invalid or missing (403 Forbidden)
    
    Example:
        @app.get("/admin/servers", dependencies=[Depends(verify_admin_api_key)])
        async def list_servers():
            ...
    """
    # Check if API key matches
    if x_api_key != settings.admin_api_key:
        logger.warning(
            f"Invalid admin API key attempt (key starts with: {x_api_key[:8]}...)"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "message": "Invalid or missing admin API key",
                    "type": "authentication_error",
                    "code": "invalid_api_key"
                }
            }
        )
    
    logger.debug("Admin API key verified successfully")
    return x_api_key


async def verify_client_api_key(
    x_api_key: Annotated[str | None, Header(description="Client API key")] = None
) -> str | None:
    """Dependency to verify client API key (if required).
    
    This function is used as a FastAPI dependency for client inference endpoints.
    If client API keys are required, it validates the key. Otherwise, it allows
    access without a key.
    
    Args:
        x_api_key: Optional API key from X-API-Key header
    
    Returns:
        The validated API key, or None if not required
    
    Raises:
        HTTPException: If API key is required but invalid/missing (403 Forbidden)
    """
    # If client API keys are not required, allow access
    if not settings.require_client_api_key:
        return None
    
    # Client API keys are required
    if not x_api_key:
        logger.warning("Client API key required but not provided")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "message": "API key required",
                    "type": "authentication_error",
                    "code": "missing_api_key"
                }
            }
        )
    
    # Check if API key is in the list of valid client keys
    if x_api_key not in settings.client_api_keys:
        logger.warning(
            f"Invalid client API key attempt (key starts with: {x_api_key[:8]}...)"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "message": "Invalid API key",
                    "type": "authentication_error",
                    "code": "invalid_api_key"
                }
            }
        )
    
    logger.debug("Client API key verified successfully")
    return x_api_key

