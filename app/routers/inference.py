"""Inference API router for OpenAI-compatible endpoints.

This module implements the inference endpoints that clients use to make
requests to hosted models. It provides OpenAI-compatible API endpoints
for chat completions, completions, and model listing.
"""

import time
import uuid
from typing import Union
from fastapi import APIRouter, HTTPException, Header, Response
from fastapi.responses import JSONResponse

from app.utils.logger import get_logger
from app.utils.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    ModelListResponse,
    ModelInfo,
    ErrorResponse,
    ErrorDetail,
)
from app.services.router import handle_request, get_healthy_servers
from app.utils.database import get_db_connection

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["inference"])


def create_error_response(
    status_code: int,
    message: str,
    error_type: str = "invalid_request_error",
    param: str = None
) -> JSONResponse:
    """Create an OpenAI-compatible error response.

    Args:
        status_code: HTTP status code
        message: Error message
        error_type: Type of error
        param: Parameter that caused the error (optional)

    Returns:
        JSONResponse with error details
    """
    error = ErrorResponse(
        error=ErrorDetail(
            message=message,
            type=error_type,
            param=param,
            code=str(status_code)
        )
    )

    logger.error(
        f"Returning error response: {status_code} - {message}",
        extra={
            "error_type": error_type,
            "status_code": status_code,
            "param": param
        }
    )

    return JSONResponse(
        status_code=status_code,
        content=error.model_dump()
    )


@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """List all available models.

    Returns a list of models that have at least one healthy server registered.
    This endpoint matches the OpenAI /v1/models API format.

    Returns:
        ModelListResponse with list of available models
    """
    logger.info("Received request to list available models")

    try:
        conn = await get_db_connection()

        # Query for unique models with at least one healthy server
        query = """
            SELECT DISTINCT model_name
            FROM model_servers
            WHERE health_status = 'healthy'
                AND is_active = 1
            ORDER BY model_name
        """

        cursor = await conn.execute(query)
        rows = await cursor.fetchall()
        model_names = [row[0] for row in rows]

        await conn.close()

        # Create model info objects
        models = [
            ModelInfo(
                id=model_name,
                object="model",
                created=int(time.time()),
                owned_by="system"
            )
            for model_name in model_names
        ]

        logger.info(f"Returning {len(models)} available model(s): {model_names}")

        return ModelListResponse(
            object="list",
            data=models
        )

    except Exception as exc:
        logger.error(f"Error listing models: {str(exc)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error while listing models"
        )


@router.post("/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    response: Response
):
    """Create a chat completion using the specified model.

    This endpoint matches the OpenAI /v1/chat/completions API format.
    It routes the request to a healthy server hosting the requested model.

    Args:
        request: ChatCompletionRequest with messages and parameters
        response: FastAPI Response object for setting headers

    Returns:
        ChatCompletionResponse from the backend server

    Raises:
        HTTPException: If model not found or all servers unhealthy
    """
    logger.info(
        f"Received chat completion request for model '{request.model}'",
        extra={
            "model": request.model,
            "num_messages": len(request.messages),
            "stream": request.stream
        }
    )

    # Validate stream parameter (Phase 3 only supports non-streaming)
    if request.stream:
        logger.warning("Streaming requested but not yet supported in Phase 3")
        return create_error_response(
            status_code=400,
            message="Streaming is not yet supported. Please set 'stream': false",
            error_type="invalid_request_error",
            param="stream"
        )

    # Convert request to dict for forwarding
    request_data = request.model_dump(exclude_none=True)

    # Route the request
    status_code, response_data, error_msg, server_id = await handle_request(
        model_name=request.model,
        endpoint="/v1/chat/completions",
        request_data=request_data,
        max_retries=2
    )

    # Add custom header to indicate which server handled the request
    if server_id:
        response.headers["X-Gateway-Server-ID"] = server_id

    # Handle errors
    if status_code == 503:
        return create_error_response(
            status_code=503,
            message=error_msg or "No healthy servers available for this model",
            error_type="service_unavailable_error"
        )
    elif status_code == 504:
        return create_error_response(
            status_code=504,
            message=error_msg or "All servers failed to respond",
            error_type="gateway_timeout_error"
        )
    elif status_code != 200:
        return create_error_response(
            status_code=status_code,
            message=error_msg or "Request failed",
            error_type="server_error"
        )

    # Return successful response
    logger.info(
        f"Successfully completed chat completion request for model '{request.model}'",
        extra={"server_id": server_id}
    )

    return JSONResponse(content=response_data)


@router.post("/completions")
async def create_completion(
    request: CompletionRequest,
    response: Response
):
    """Create a text completion using the specified model.

    This endpoint matches the OpenAI /v1/completions API format.
    It routes the request to a healthy server hosting the requested model.

    Args:
        request: CompletionRequest with prompt and parameters
        response: FastAPI Response object for setting headers

    Returns:
        CompletionResponse from the backend server

    Raises:
        HTTPException: If model not found or all servers unhealthy
    """
    logger.info(
        f"Received completion request for model '{request.model}'",
        extra={
            "model": request.model,
            "prompt_type": type(request.prompt).__name__,
            "stream": request.stream
        }
    )

    # Validate stream parameter (Phase 3 only supports non-streaming)
    if request.stream:
        logger.warning("Streaming requested but not yet supported in Phase 3")
        return create_error_response(
            status_code=400,
            message="Streaming is not yet supported. Please set 'stream': false",
            error_type="invalid_request_error",
            param="stream"
        )

    # Convert request to dict for forwarding
    request_data = request.model_dump(exclude_none=True)

    # Route the request
    status_code, response_data, error_msg, server_id = await handle_request(
        model_name=request.model,
        endpoint="/v1/completions",
        request_data=request_data,
        max_retries=2
    )

    # Add custom header to indicate which server handled the request
    if server_id:
        response.headers["X-Gateway-Server-ID"] = server_id

    # Handle errors
    if status_code == 503:
        return create_error_response(
            status_code=503,
            message=error_msg or "No healthy servers available for this model",
            error_type="service_unavailable_error"
        )
    elif status_code == 504:
        return create_error_response(
            status_code=504,
            message=error_msg or "All servers failed to respond",
            error_type="gateway_timeout_error"
        )
    elif status_code != 200:
        return create_error_response(
            status_code=status_code,
            message=error_msg or "Request failed",
            error_type="server_error"
        )

    # Return successful response
    logger.info(
        f"Successfully completed completion request for model '{request.model}'",
        extra={"server_id": server_id}
    )

    return JSONResponse(content=response_data)
