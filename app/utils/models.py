"""Pydantic models for API requests and responses.

This module contains all data models used in the API, including:
- Registration request/response models
- Server listing models
- Error models
- Inference request/response models (OpenAI-compatible)
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Registration Models
# =============================================================================

class RegisterServerRequest(BaseModel):
    """Request model for registering a new server.
    
    This model validates the incoming registration request and ensures
    all required fields are present and valid.
    """
    
    model_name: str = Field(
        ...,
        description="Name of the model being served (e.g., 'llama-2-7b', 'gpt-3.5-turbo')",
        min_length=1,
        max_length=100,
        examples=["llama-2-7b", "mistral-7b-instruct"]
    )
    
    endpoint_url: str = Field(
        ...,
        description="Full URL of the model server endpoint (must be publicly accessible)",
        min_length=1,
        max_length=500,
        examples=["https://abc123.ngrok.io", "https://model.example.com"]
    )
    
    api_key: Optional[str] = Field(
        None,
        description="API key required to access the backend server (if any)",
        max_length=200
    )
    
    owner_name: Optional[str] = Field(
        None,
        description="Name of the person hosting the server",
        max_length=100,
        examples=["Jane Doe"]
    )
    
    owner_email: Optional[str] = Field(
        None,
        description="Email address of the server owner",
        max_length=100,
        examples=["jane@example.com"]
    )
    
    description: Optional[str] = Field(
        None,
        description="Optional description of the model or server",
        max_length=500
    )
    
    tags: Optional[str] = Field(
        None,
        description="Comma-separated tags for categorization",
        max_length=200,
        examples=["llm,instruct,7b"]
    )
    
    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, value: str) -> str:
        """Validate model name contains only allowed characters."""
        # Allow alphanumeric, hyphens, underscores, dots
        import re
        if not re.match(r'^[a-zA-Z0-9._-]+$', value):
            raise ValueError(
                "model_name must contain only alphanumeric characters, "
                "hyphens, underscores, and dots"
            )
        return value
    
    @field_validator("endpoint_url")
    @classmethod
    def validate_endpoint_url(cls, value: str) -> str:
        """Basic URL format validation."""
        if not value.startswith(("http://", "https://")):
            raise ValueError("endpoint_url must start with http:// or https://")
        return value.rstrip("/")  # Remove trailing slash


class RegisterServerResponse(BaseModel):
    """Response model for successful server registration."""
    
    registration_id: str = Field(
        ...,
        description="Unique registration ID for this server"
    )
    
    model_name: str = Field(
        ...,
        description="Name of the registered model"
    )
    
    endpoint_url: str = Field(
        ...,
        description="URL of the registered server"
    )
    
    health_status: str = Field(
        ...,
        description="Current health status of the server"
    )
    
    message: str = Field(
        ...,
        description="Success message"
    )
    
    created_at: str = Field(
        ...,
        description="Timestamp when the server was registered"
    )


class UpdateServerRequest(BaseModel):
    """Request model for updating server details.
    
    All fields are optional - only provide fields you want to update.
    """
    
    model_name: Optional[str] = Field(
        None,
        description="New model name",
        min_length=1,
        max_length=100
    )
    
    endpoint_url: Optional[str] = Field(
        None,
        description="New endpoint URL",
        min_length=1,
        max_length=500
    )
    
    api_key: Optional[str] = Field(
        None,
        description="New API key (use empty string to remove)",
        max_length=200
    )
    
    owner_name: Optional[str] = Field(
        None,
        description="New owner name",
        max_length=100
    )
    
    owner_email: Optional[str] = Field(
        None,
        description="New owner email",
        max_length=100
    )
    
    description: Optional[str] = Field(
        None,
        description="New description",
        max_length=500
    )
    
    tags: Optional[str] = Field(
        None,
        description="New tags",
        max_length=200
    )
    
    @field_validator("endpoint_url")
    @classmethod
    def validate_endpoint_url(cls, value: Optional[str]) -> Optional[str]:
        """Basic URL format validation."""
        if value is not None:
            if not value.startswith(("http://", "https://")):
                raise ValueError("endpoint_url must start with http:// or https://")
            return value.rstrip("/")
        return value


# =============================================================================
# Server Listing Models
# =============================================================================

class ServerListItem(BaseModel):
    """Model for a single server in the listing."""
    
    id: int = Field(
        ...,
        description="Internal database ID"
    )
    
    registration_id: str = Field(
        ...,
        description="Unique registration ID"
    )
    
    model_name: str = Field(
        ...,
        description="Name of the model"
    )
    
    endpoint_url: str = Field(
        ...,
        description="Server endpoint URL"
    )
    
    owner_name: Optional[str] = Field(
        None,
        description="Owner name"
    )
    
    owner_email: Optional[str] = Field(
        None,
        description="Owner email"
    )
    
    health_status: str = Field(
        ...,
        description="Current health status (healthy, unhealthy, unknown)"
    )
    
    consecutive_failures: int = Field(
        ...,
        description="Number of consecutive health check failures"
    )
    
    last_checked_at: Optional[str] = Field(
        None,
        description="Timestamp of last health check"
    )
    
    last_successful_request_at: Optional[str] = Field(
        None,
        description="Timestamp of last successful request"
    )
    
    is_active: bool = Field(
        ...,
        description="Whether the server is active"
    )
    
    created_at: str = Field(
        ...,
        description="Timestamp when server was registered"
    )
    
    updated_at: str = Field(
        ...,
        description="Timestamp when server was last updated"
    )
    
    description: Optional[str] = Field(
        None,
        description="Server description"
    )
    
    tags: Optional[str] = Field(
        None,
        description="Server tags"
    )


class ServerListResponse(BaseModel):
    """Response model for listing servers."""
    
    servers: List[ServerListItem] = Field(
        ...,
        description="List of registered servers"
    )
    
    total: int = Field(
        ...,
        description="Total number of servers"
    )
    
    filters_applied: dict = Field(
        default_factory=dict,
        description="Filters that were applied to the listing"
    )


# =============================================================================
# Error Models (OpenAI-compatible)
# =============================================================================

class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    
    type: str = Field(
        ...,
        description="Error type/code"
    )
    
    param: Optional[str] = Field(
        None,
        description="Parameter that caused the error (if applicable)"
    )
    
    code: Optional[str] = Field(
        None,
        description="Error code for programmatic handling"
    )


class ErrorResponse(BaseModel):
    """OpenAI-compatible error response format."""
    
    error: ErrorDetail = Field(
        ...,
        description="Error details"
    )


# =============================================================================
# Health Check Models
# =============================================================================

class HealthCheckResult(BaseModel):
    """Result of a health check operation."""
    
    server_id: int = Field(
        ...,
        description="Database ID of the server"
    )
    
    registration_id: str = Field(
        ...,
        description="Registration ID of the server"
    )
    
    endpoint_url: str = Field(
        ...,
        description="URL that was checked"
    )
    
    is_healthy: bool = Field(
        ...,
        description="Whether the server is healthy"
    )
    
    response_time_ms: Optional[int] = Field(
        None,
        description="Response time in milliseconds"
    )
    
    error_message: Optional[str] = Field(
        None,
        description="Error message if health check failed"
    )
    
    checked_at: str = Field(
        ...,
        description="Timestamp of the check"
    )


# =============================================================================
# Success Response Models
# =============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = Field(
        True,
        description="Indicates successful operation"
    )

    message: str = Field(
        ...,
        description="Success message"
    )

    data: Optional[dict] = Field(
        None,
        description="Additional data (if any)"
    )


# =============================================================================
# Inference API Models (OpenAI-compatible)
# =============================================================================

class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    role: Literal["system", "user", "assistant", "function"] = Field(
        ...,
        description="The role of the message author"
    )

    content: str = Field(
        ...,
        description="The content of the message"
    )

    name: Optional[str] = Field(
        None,
        description="The name of the author (optional)"
    )


class ChatCompletionRequest(BaseModel):
    """Request model for chat completions endpoint.

    Matches OpenAI's chat completion API format.
    """

    model: str = Field(
        ...,
        description="ID of the model to use",
        examples=["llama-2-7b", "gpt-3.5-turbo"]
    )

    messages: List[ChatMessage] = Field(
        ...,
        description="A list of messages comprising the conversation so far"
    )

    temperature: Optional[float] = Field(
        1.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature to use"
    )

    top_p: Optional[float] = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )

    n: Optional[int] = Field(
        1,
        ge=1,
        description="Number of completions to generate"
    )

    stream: Optional[bool] = Field(
        False,
        description="Whether to stream back partial progress"
    )

    stop: Optional[Union[str, List[str]]] = Field(
        None,
        description="Up to 4 sequences where the API will stop generating"
    )

    max_tokens: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum number of tokens to generate"
    )

    presence_penalty: Optional[float] = Field(
        0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty parameter"
    )

    frequency_penalty: Optional[float] = Field(
        0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty parameter"
    )

    logit_bias: Optional[Dict[str, float]] = Field(
        None,
        description="Modify likelihood of specified tokens"
    )

    user: Optional[str] = Field(
        None,
        description="Unique identifier for the end-user"
    )


class CompletionRequest(BaseModel):
    """Request model for completions endpoint.

    Matches OpenAI's completion API format.
    """

    model: str = Field(
        ...,
        description="ID of the model to use",
        examples=["llama-2-7b", "gpt-3.5-turbo"]
    )

    prompt: Union[str, List[str]] = Field(
        ...,
        description="The prompt(s) to generate completions for"
    )

    temperature: Optional[float] = Field(
        1.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature to use"
    )

    top_p: Optional[float] = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling parameter"
    )

    n: Optional[int] = Field(
        1,
        ge=1,
        description="Number of completions to generate"
    )

    stream: Optional[bool] = Field(
        False,
        description="Whether to stream back partial progress"
    )

    stop: Optional[Union[str, List[str]]] = Field(
        None,
        description="Up to 4 sequences where the API will stop generating"
    )

    max_tokens: Optional[int] = Field(
        16,
        ge=1,
        description="Maximum number of tokens to generate"
    )

    presence_penalty: Optional[float] = Field(
        0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty parameter"
    )

    frequency_penalty: Optional[float] = Field(
        0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty parameter"
    )

    logit_bias: Optional[Dict[str, float]] = Field(
        None,
        description="Modify likelihood of specified tokens"
    )

    user: Optional[str] = Field(
        None,
        description="Unique identifier for the end-user"
    )


class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(
        ...,
        description="Number of tokens in the prompt"
    )

    completion_tokens: int = Field(
        ...,
        description="Number of tokens in the completion"
    )

    total_tokens: int = Field(
        ...,
        description="Total number of tokens used"
    )


class ChatCompletionChoice(BaseModel):
    """A single chat completion choice."""

    index: int = Field(
        ...,
        description="The index of this choice"
    )

    message: ChatMessage = Field(
        ...,
        description="The message generated by the model"
    )

    finish_reason: Optional[str] = Field(
        None,
        description="The reason the model stopped generating tokens"
    )


class ChatCompletionResponse(BaseModel):
    """Response model for chat completions endpoint.

    Matches OpenAI's chat completion response format.
    """

    id: str = Field(
        ...,
        description="Unique identifier for this completion"
    )

    object: str = Field(
        "chat.completion",
        description="Object type"
    )

    created: int = Field(
        ...,
        description="Unix timestamp of when the completion was created"
    )

    model: str = Field(
        ...,
        description="The model used for completion"
    )

    choices: List[ChatCompletionChoice] = Field(
        ...,
        description="List of completion choices"
    )

    usage: Optional[Usage] = Field(
        None,
        description="Token usage information"
    )


class CompletionChoice(BaseModel):
    """A single completion choice."""

    index: int = Field(
        ...,
        description="The index of this choice"
    )

    text: str = Field(
        ...,
        description="The generated text"
    )

    finish_reason: Optional[str] = Field(
        None,
        description="The reason the model stopped generating tokens"
    )

    logprobs: Optional[Dict[str, Any]] = Field(
        None,
        description="Log probabilities of tokens (if requested)"
    )


class CompletionResponse(BaseModel):
    """Response model for completions endpoint.

    Matches OpenAI's completion response format.
    """

    id: str = Field(
        ...,
        description="Unique identifier for this completion"
    )

    object: str = Field(
        "text_completion",
        description="Object type"
    )

    created: int = Field(
        ...,
        description="Unix timestamp of when the completion was created"
    )

    model: str = Field(
        ...,
        description="The model used for completion"
    )

    choices: List[CompletionChoice] = Field(
        ...,
        description="List of completion choices"
    )

    usage: Optional[Usage] = Field(
        None,
        description="Token usage information"
    )


class ModelInfo(BaseModel):
    """Information about a single model."""

    id: str = Field(
        ...,
        description="Model identifier"
    )

    object: str = Field(
        "model",
        description="Object type"
    )

    created: Optional[int] = Field(
        None,
        description="Unix timestamp of model creation"
    )

    owned_by: str = Field(
        "system",
        description="Organization that owns the model"
    )


class ModelListResponse(BaseModel):
    """Response model for /v1/models endpoint.

    Matches OpenAI's models list response format.
    """

    object: str = Field(
        "list",
        description="Object type"
    )

    data: List[ModelInfo] = Field(
        ...,
        description="List of available models"
    )

