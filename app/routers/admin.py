"""Admin API router for server registration and management.

This module provides endpoints for:
- Registering new model servers
- Deregistering servers
- Updating server details
- Listing all registered servers
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from app.utils.auth import verify_admin_api_key
from app.utils.config import get_settings
from app.utils.logger import get_logger
from app.utils.models import (
    RegisterServerRequest,
    RegisterServerResponse,
    UpdateServerRequest,
    ServerListResponse,
    SuccessResponse,
    ErrorResponse
)
from app.utils.validation import validate_url
from app.services.registry import (
    register_server,
    deregister_server,
    update_server,
    list_servers,
    get_server_by_registration_id,
    get_server_count,
    get_model_count
)
from app.services.health import perform_initial_health_check

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(verify_admin_api_key)],  # All endpoints require admin API key
)


@router.post(
    "/register",
    response_model=RegisterServerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new model server",
    description=(
        "Register a new model server with the gateway. The server must be "
        "publicly accessible and implement the OpenAI-compatible /v1/models endpoint. "
        "An initial health check will be performed before accepting the registration."
    ),
    responses={
        201: {
            "description": "Server registered successfully",
            "model": RegisterServerResponse
        },
        400: {
            "description": "Invalid request (bad URL, validation failed)",
            "model": ErrorResponse
        },
        403: {
            "description": "Invalid or missing admin API key",
            "model": ErrorResponse
        },
        503: {
            "description": "Initial health check failed",
            "model": ErrorResponse
        }
    }
)
async def register_model_server(
    request: RegisterServerRequest
) -> RegisterServerResponse:
    """Register a new model server.
    
    The registration process:
    1. Validates the endpoint URL
    2. Performs an initial health check
    3. Registers the server in the database
    4. Returns registration details
    
    Args:
        request: Server registration details
    
    Returns:
        RegisterServerResponse with registration ID and details
    
    Raises:
        HTTPException: If validation or health check fails
    """
    logger.info(
        f"Received registration request for model '{request.model_name}' "
        f"at {request.endpoint_url}"
    )
    
    # Validate URL
    is_valid, error_message = validate_url(request.endpoint_url)
    if not is_valid:
        logger.warning(
            f"Registration rejected: Invalid URL - {error_message}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "message": f"Invalid endpoint URL: {error_message}",
                    "type": "invalid_request_error",
                    "param": "endpoint_url",
                    "code": "invalid_url"
                }
            }
        )
    
    try:
        # Register server in database (initially with "unknown" health status)
        server_data = await register_server(
            model_name=request.model_name,
            endpoint_url=request.endpoint_url,
            api_key=request.api_key,
            owner_name=request.owner_name,
            owner_email=request.owner_email,
            description=request.description,
            tags=request.tags,
            initial_health_status="unknown"
        )
        
        # Perform initial health check
        is_healthy, health_error = await perform_initial_health_check(
            server_id=server_data["id"],
            registration_id=server_data["registration_id"],
            endpoint_url=request.endpoint_url,
            api_key=request.api_key
        )
        
        # Update health status in response
        if is_healthy:
            health_status = "healthy"
            logger.info(
                f"Server {server_data['registration_id']} registered successfully "
                f"and passed initial health check"
            )
        else:
            health_status = "unhealthy"
            logger.warning(
                f"Server {server_data['registration_id']} registered but "
                f"failed initial health check: {health_error}"
            )
            # Still accept registration, but warn about health
            # Note: Could optionally reject here if desired
        
        # Import here to avoid circular dependency
        from app.services.registry import update_health_status
        await update_health_status(
            server_id=server_data["id"],
            is_healthy=is_healthy,
            error_message=health_error
        )
        
        return RegisterServerResponse(
            registration_id=server_data["registration_id"],
            model_name=server_data["model_name"],
            endpoint_url=server_data["endpoint_url"],
            health_status=health_status,
            message="Server registered successfully",
            created_at=server_data["created_at"]
        )
    
    except Exception as error:
        logger.error(
            f"Failed to register server: {error}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "message": "Failed to register server",
                    "type": "server_error",
                    "code": "registration_failed"
                }
            }
        )


@router.delete(
    "/register/{registration_id}",
    response_model=SuccessResponse,
    summary="Deregister a server",
    description=(
        "Remove a server from the gateway. After deregistration, no new requests "
        "will be routed to this server."
    ),
    responses={
        200: {
            "description": "Server deregistered successfully",
            "model": SuccessResponse
        },
        403: {
            "description": "Invalid or missing admin API key",
            "model": ErrorResponse
        },
        404: {
            "description": "Server not found",
            "model": ErrorResponse
        }
    }
)
async def deregister_model_server(
    registration_id: str
) -> SuccessResponse:
    """Deregister a server.
    
    Args:
        registration_id: The registration ID of the server to deregister
    
    Returns:
        Success confirmation message
    
    Raises:
        HTTPException: If server not found
    """
    logger.info(f"Received deregistration request for server {registration_id}")
    
    try:
        success = await deregister_server(registration_id)
        
        if success:
            return SuccessResponse(
                success=True,
                message=f"Server {registration_id} deregistered successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "message": f"Server not found: {registration_id}",
                        "type": "invalid_request_error",
                        "param": "registration_id",
                        "code": "server_not_found"
                    }
                }
            )
    
    except HTTPException:
        raise
    except Exception as error:
        logger.error(
            f"Failed to deregister server {registration_id}: {error}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "message": "Failed to deregister server",
                    "type": "server_error",
                    "code": "deregistration_failed"
                }
            }
        )


@router.put(
    "/register/{registration_id}",
    response_model=SuccessResponse,
    summary="Update server details",
    description=(
        "Update the details of a registered server. Only provide the fields "
        "you want to update. If the endpoint URL is changed, a new health check "
        "will be performed."
    ),
    responses={
        200: {
            "description": "Server updated successfully",
            "model": SuccessResponse
        },
        400: {
            "description": "Invalid request (bad URL, validation failed)",
            "model": ErrorResponse
        },
        403: {
            "description": "Invalid or missing admin API key",
            "model": ErrorResponse
        },
        404: {
            "description": "Server not found",
            "model": ErrorResponse
        }
    }
)
async def update_model_server(
    registration_id: str,
    request: UpdateServerRequest
) -> SuccessResponse:
    """Update server details.
    
    Args:
        registration_id: The registration ID of the server to update
        request: Fields to update
    
    Returns:
        Success confirmation message
    
    Raises:
        HTTPException: If server not found or validation fails
    """
    logger.info(f"Received update request for server {registration_id}")
    
    # Validate new endpoint URL if provided
    if request.endpoint_url is not None:
        is_valid, error_message = validate_url(request.endpoint_url)
        if not is_valid:
            logger.warning(
                f"Update rejected: Invalid URL - {error_message}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "message": f"Invalid endpoint URL: {error_message}",
                        "type": "invalid_request_error",
                        "param": "endpoint_url",
                        "code": "invalid_url"
                    }
                }
            )
    
    try:
        # Update server in database
        success = await update_server(
            registration_id=registration_id,
            model_name=request.model_name,
            endpoint_url=request.endpoint_url,
            api_key=request.api_key,
            owner_name=request.owner_name,
            owner_email=request.owner_email,
            description=request.description,
            tags=request.tags
        )
        
        if success:
            # If endpoint URL was changed, perform a health check
            if request.endpoint_url is not None:
                logger.info(
                    f"Endpoint URL changed for {registration_id}, "
                    "performing health check"
                )
                server_data = await get_server_by_registration_id(registration_id)
                if server_data:
                    is_healthy, _ = await perform_initial_health_check(
                        server_id=server_data["id"],
                        registration_id=registration_id,
                        endpoint_url=request.endpoint_url,
                        api_key=request.api_key or server_data.get("api_key")
                    )
                    from app.services.registry import update_health_status
                    await update_health_status(
                        server_id=server_data["id"],
                        is_healthy=is_healthy
                    )
            
            return SuccessResponse(
                success=True,
                message=f"Server {registration_id} updated successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "message": f"Server not found: {registration_id}",
                        "type": "invalid_request_error",
                        "param": "registration_id",
                        "code": "server_not_found"
                    }
                }
            )
    
    except HTTPException:
        raise
    except Exception as error:
        logger.error(
            f"Failed to update server {registration_id}: {error}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "message": "Failed to update server",
                    "type": "server_error",
                    "code": "update_failed"
                }
            }
        )


@router.get(
    "/servers",
    response_model=ServerListResponse,
    summary="List all registered servers",
    description=(
        "Retrieve a list of all registered servers with optional filtering "
        "by model name, health status, or active status."
    ),
    responses={
        200: {
            "description": "List of servers",
            "model": ServerListResponse
        },
        403: {
            "description": "Invalid or missing admin API key",
            "model": ErrorResponse
        }
    }
)
async def list_model_servers(
    model_name: Optional[str] = Query(
        None,
        description="Filter by model name"
    ),
    health_status: Optional[str] = Query(
        None,
        description="Filter by health status (healthy, unhealthy, unknown)"
    ),
    include_inactive: bool = Query(
        False,
        description="Include inactive/deregistered servers"
    )
) -> ServerListResponse:
    """List all registered servers.
    
    Args:
        model_name: Optional filter by model name
        health_status: Optional filter by health status
        include_inactive: Whether to include inactive servers
    
    Returns:
        ServerListResponse with list of servers and metadata
    """
    logger.info(
        f"Listing servers (model: {model_name}, status: {health_status}, "
        f"include_inactive: {include_inactive})"
    )
    
    try:
        servers = await list_servers(
            model_name=model_name,
            health_status=health_status,
            include_inactive=include_inactive
        )
        
        # Build filters_applied dict
        filters_applied = {}
        if model_name:
            filters_applied["model_name"] = model_name
        if health_status:
            filters_applied["health_status"] = health_status
        if include_inactive:
            filters_applied["include_inactive"] = include_inactive
        
        return ServerListResponse(
            servers=servers,
            total=len(servers),
            filters_applied=filters_applied
        )
    
    except Exception as error:
        logger.error(f"Failed to list servers: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "message": "Failed to list servers",
                    "type": "server_error",
                    "code": "list_failed"
                }
            }
        )


@router.get(
    "/stats",
    summary="Get gateway statistics",
    description="Retrieve statistics about registered servers and models",
    responses={
        200: {
            "description": "Gateway statistics"
        },
        403: {
            "description": "Invalid or missing admin API key",
            "model": ErrorResponse
        }
    }
)
async def get_statistics() -> JSONResponse:
    """Get gateway statistics.
    
    Returns:
        JSON response with statistics
    """
    try:
        total_servers = await get_server_count()
        total_models = await get_model_count()
        
        # Get servers by health status
        healthy_servers = await list_servers(health_status="healthy")
        unhealthy_servers = await list_servers(health_status="unhealthy")
        unknown_servers = await list_servers(health_status="unknown")
        
        return JSONResponse(
            content={
                "total_servers": total_servers,
                "total_models": total_models,
                "servers_by_health": {
                    "healthy": len(healthy_servers),
                    "unhealthy": len(unhealthy_servers),
                    "unknown": len(unknown_servers)
                }
            }
        )
    
    except Exception as error:
        logger.error(f"Failed to get statistics: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "message": "Failed to get statistics",
                    "type": "server_error",
                    "code": "stats_failed"
                }
            }
        )

