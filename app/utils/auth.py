"""Authentication utilities for the inference gateway.

This module provides functions and dependencies for API key and session-based authentication.
"""

from typing import Annotated, Optional
from fastapi import Header, HTTPException, status, Request

from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Import session auth (lazy import to avoid circular dependencies)
_session_authenticator = None


def get_session_auth():
    """Lazy load session authenticator."""
    global _session_authenticator
    if _session_authenticator is None:
        try:
            from app.utils.session_auth import get_session_authenticator
            _session_authenticator = get_session_authenticator()
        except Exception as error:
            logger.warning(f"Session auth not available: {error}")
            _session_authenticator = False  # Mark as unavailable
    return _session_authenticator if _session_authenticator is not False else None


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


async def verify_admin_auth(
    request: Request,
    x_api_key: Annotated[Optional[str], Header(description="Admin API key")] = None
) -> dict:
    """Verify admin authentication via session or API key.
    
    This dependency tries two authentication methods in order:
    1. Session-based auth: Check if user is logged in via multiverse.school session
    2. API key auth: Fall back to X-API-Key header validation
    
    Args:
        request: FastAPI request object (for session cookie)
        x_api_key: Optional API key from X-API-Key header
    
    Returns:
        Authentication info dict with 'method' and optional 'user' data
    
    Raises:
        HTTPException: If neither authentication method succeeds (403 Forbidden)
    """
    # Try session-based authentication first
    session_auth = get_session_auth()
    if session_auth:
        try:
            is_admin = await session_auth.is_admin(request)
            if is_admin:
                # Get full user details
                session_id = session_auth.get_session_cookie(request)
                if session_id:
                    session_data = await session_auth.validate_session(session_id)
                    if session_data:
                        user = await session_auth.get_user_from_session(session_data)
                        if user:
                            logger.debug(f"Admin authenticated via session: {user.get('email')}")
                            return {
                                'method': 'session',
                                'user': user
                            }
        except Exception as error:
            logger.debug(f"Session auth failed: {error}")
    
    # Fall back to API key authentication
    if x_api_key and x_api_key == settings.admin_api_key:
        logger.debug("Admin authenticated via API key")
        return {
            'method': 'api_key',
            'api_key': x_api_key
        }
    
    # Neither authentication method succeeded
    if x_api_key:
        logger.warning(f"Invalid admin API key attempt (key starts with: {x_api_key[:8]}...)")
    else:
        logger.warning("Admin access attempt without valid session or API key")
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": {
                "message": "Authentication required. Please log in or provide a valid admin API key.",
                "type": "authentication_error",
                "code": "authentication_required"
            }
        }
    )

