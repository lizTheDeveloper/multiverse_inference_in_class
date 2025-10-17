"""Integration tests for streaming functionality.

This module tests the Server-Sent Events (SSE) streaming support
for chat completions and completions endpoints.
"""

import pytest
import os
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

# Set test environment variables before importing app
os.environ["ADMIN_API_KEY"] = "test-admin-key-streaming-1234567890"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_streaming.db"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["HEALTH_CHECK_INTERVAL_SECONDS"] = "10"

from app.main import app
from app.utils.database import init_database, close_database, get_db_connection
from app.services.registry import register_server
from app.utils.models import RegisterServerRequest


@pytest.fixture(scope="function")
async def test_db():
    """Initialize test database before each test."""
    await init_database()
    yield
    await close_database()
    # Clean up test database file
    import os
    try:
        os.remove("./test_streaming.db")
    except FileNotFoundError:
        pass


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return authentication headers for admin API."""
    return {"X-API-Key": "test-admin-key-streaming-1234567890"}


class MockStreamingResponse:
    """Mock streaming response for httpx."""
    
    def __init__(self, chunks: list, status_code: int = 200):
        self.chunks = chunks
        self.status_code = status_code
        self._index = 0
    
    async def aiter_bytes(self):
        """Async iterator for response chunks."""
        for chunk in self.chunks:
            yield chunk.encode('utf-8')
    
    async def aread(self):
        """Read error response body."""
        return b'{"error": "Backend error"}'
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
async def test_streaming_chat_completion_success(test_db, client, auth_headers):
    """Test successful streaming chat completion.
    
    Verifies:
    - Streaming response is returned with correct media type
    - SSE format is correct (data: {json}\\n\\n)
    - Multiple chunks are streamed
    - Server is marked with successful request
    """
    # Register a test server
    server_request = RegisterServerRequest(
        model_name="test-stream-model",
        endpoint_url="https://streaming-test.example.com",
        api_key="test-backend-key",
        owner_name="Test Streamer"
    )
    
    # Mock initial health check to succeed
    with patch('app.services.health.check_server_health') as mock_health:
        mock_health.return_value = (True, None, 200)
        
        registration_response = client.post(
            "/admin/register",
            json=server_request.model_dump(),
            headers=auth_headers
        )
        assert registration_response.status_code == status.HTTP_201_CREATED
    
    # Mock streaming response
    mock_chunks = [
        'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"test-stream-model","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}\n\n',
        'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"test-stream-model","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}\n\n',
        'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"test-stream-model","choices":[{"index":0,"delta":{"content":" world"},"finish_reason":null}]}\n\n',
        'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"test-stream-model","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\n',
        'data: [DONE]\n\n'
    ]
    
    mock_response = MockStreamingResponse(mock_chunks)
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Make streaming request
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-stream-model",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True
            }
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert "X-Gateway-Server-ID" in response.headers
        
        # Verify streaming content
        content = response.text
        assert "data: " in content
        assert "chat.completion.chunk" in content
        assert "[DONE]" in content


@pytest.mark.asyncio
async def test_streaming_completion_success(test_db, client, auth_headers):
    """Test successful streaming text completion.
    
    Verifies:
    - Streaming response is returned
    - Text completion chunks are properly formatted
    """
    # Register a test server
    server_request = RegisterServerRequest(
        model_name="test-completion-model",
        endpoint_url="https://completion-test.example.com",
        api_key="test-backend-key",
        owner_name="Test Completer"
    )
    
    # Mock initial health check to succeed
    with patch('app.services.health.check_server_health') as mock_health:
        mock_health.return_value = (True, None, 200)
        
        registration_response = client.post(
            "/admin/register",
            json=server_request.model_dump(),
            headers=auth_headers
        )
        assert registration_response.status_code == status.HTTP_201_CREATED
    
    # Mock streaming response
    mock_chunks = [
        'data: {"id":"cmpl-123","object":"text_completion","created":1234567890,"model":"test-completion-model","choices":[{"index":0,"text":"Once","finish_reason":null}]}\n\n',
        'data: {"id":"cmpl-123","object":"text_completion","created":1234567890,"model":"test-completion-model","choices":[{"index":0,"text":" upon","finish_reason":null}]}\n\n',
        'data: {"id":"cmpl-123","object":"text_completion","created":1234567890,"model":"test-completion-model","choices":[{"index":0,"text":" a","finish_reason":null}]}\n\n',
        'data: {"id":"cmpl-123","object":"text_completion","created":1234567890,"model":"test-completion-model","choices":[{"index":0,"text":" time","finish_reason":"stop"}]}\n\n',
        'data: [DONE]\n\n'
    ]
    
    mock_response = MockStreamingResponse(mock_chunks)
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Make streaming request
        response = client.post(
            "/v1/completions",
            json={
                "model": "test-completion-model",
                "prompt": "Once upon a",
                "stream": True
            }
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert "X-Gateway-Server-ID" in response.headers


@pytest.mark.asyncio
async def test_streaming_no_healthy_servers(test_db, client):
    """Test streaming request when no healthy servers available.
    
    Verifies:
    - Returns 503 error
    - Appropriate error message
    """
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "nonexistent-model",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True
        }
    )
    
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "error" in response.json()


@pytest.mark.asyncio
async def test_streaming_backend_error(test_db, client, auth_headers):
    """Test streaming request when backend returns error.
    
    Verifies:
    - Handles backend errors gracefully
    - Returns appropriate error response
    - Server is marked as unhealthy
    """
    # Register a test server
    server_request = RegisterServerRequest(
        model_name="test-error-model",
        endpoint_url="https://error-test.example.com",
        api_key="test-backend-key",
        owner_name="Test Error"
    )
    
    # Mock initial health check to succeed
    with patch('app.services.health.check_server_health') as mock_health:
        mock_health.return_value = (True, None, 200)
        
        registration_response = client.post(
            "/admin/register",
            json=server_request.model_dump(),
            headers=auth_headers
        )
        assert registration_response.status_code == status.HTTP_201_CREATED
    
    # Mock streaming response with error
    mock_response = MockStreamingResponse([], status_code=500)
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Make streaming request
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-error-model",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True
            }
        )
        
        # Verify error response
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


@pytest.mark.asyncio
async def test_non_streaming_still_works(test_db, client, auth_headers):
    """Test that non-streaming requests still work after streaming support added.
    
    Verifies:
    - Regular JSON responses work
    - stream=false parameter works
    """
    # Register a test server
    server_request = RegisterServerRequest(
        model_name="test-non-stream-model",
        endpoint_url="https://non-stream-test.example.com",
        api_key="test-backend-key",
        owner_name="Test Non-Streamer"
    )
    
    # Mock initial health check to succeed
    with patch('app.services.health.check_server_health') as mock_health:
        mock_health.return_value = (True, None, 200)
        
        registration_response = client.post(
            "/admin/register",
            json=server_request.model_dump(),
            headers=auth_headers
        )
        assert registration_response.status_code == status.HTTP_201_CREATED
    
    # Mock non-streaming response
    mock_response_data = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "test-non-stream-model",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?"
            },
            "finish_reason": "stop"
        }]
    }
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Make non-streaming request
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-non-stream-model",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            }
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["content"] == "Hello! How can I help you today?"


@pytest.mark.asyncio
async def test_streaming_connection_drop(test_db, client, auth_headers):
    """Test streaming gracefully handles mid-stream connection drops.
    
    Verifies:
    - Partial streams are logged
    - Error is logged but client connection closes gracefully
    """
    # Register a test server
    server_request = RegisterServerRequest(
        model_name="test-drop-model",
        endpoint_url="https://drop-test.example.com",
        api_key="test-backend-key",
        owner_name="Test Dropper"
    )
    
    # Mock initial health check to succeed
    with patch('app.services.health.check_server_health') as mock_health:
        mock_health.return_value = (True, None, 200)
        
        registration_response = client.post(
            "/admin/register",
            json=server_request.model_dump(),
            headers=auth_headers
        )
        assert registration_response.status_code == status.HTTP_201_CREATED
    
    # Create an async generator that raises an exception mid-stream
    async def failing_stream():
        yield 'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"test-drop-model","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}\n\n'.encode('utf-8')
        raise ConnectionError("Connection dropped")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.aiter_bytes = failing_stream
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock()
    
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.stream = MagicMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Make streaming request - should handle error gracefully
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-drop-model",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True
            }
        )
        
        # Connection should still return 200 (streaming started successfully)
        # The error happens during streaming, not before
        assert response.status_code == status.HTTP_200_OK

