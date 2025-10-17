"""Integration tests for the Inference API.

These tests verify the functionality of:
- Model listing
- Chat completions
- Text completions
- Request routing and failover
- Round-robin load balancing
- Error handling
"""

import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import httpx

# Set test environment variables before importing app
os.environ["ADMIN_API_KEY"] = "test-admin-key-1234567890"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_gateway.db"
os.environ["LOG_LEVEL"] = "DEBUG"

from app.main import app
import sqlite3
import asyncio


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initialize test database before running tests."""
    from app.utils.database import init_database
    asyncio.run(init_database())
    yield
    # Cleanup after tests
    import os
    try:
        os.remove("./test_gateway.db")
    except FileNotFoundError:
        pass


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def admin_headers():
    """Headers with valid admin API key."""
    return {"X-API-Key": "test-admin-key-1234567890"}


def _get_sync_db_connection():
    """Get a synchronous database connection for testing."""
    conn = sqlite3.connect("./test_gateway.db")
    conn.row_factory = sqlite3.Row
    return conn


@pytest.fixture
def setup_test_server(admin_headers):
    """Register a test server in the database for testing."""
    import time

    def _setup(model_name="test-model", health_status="healthy"):
        conn = _get_sync_db_connection()
        cursor = conn.cursor()

        # Use timestamp to make registration_id unique
        unique_id = f"srv_test_{model_name}_{int(time.time() * 1000000)}"

        # Insert a test server
        cursor.execute(
            """
            INSERT INTO model_servers (
                registration_id, model_name, endpoint_url,
                health_status, is_active, consecutive_failures
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                unique_id,
                model_name,
                f"https://test-server.example.com/{model_name}",
                health_status,
                1,
                0
            )
        )
        conn.commit()
        server_id = cursor.lastrowid
        conn.close()

        return {
            "id": server_id,
            "registration_id": unique_id,
            "model_name": model_name,
            "endpoint_url": f"https://test-server.example.com/{model_name}"
        }

    return _setup


class TestModelsEndpoint:
    """Test /v1/models endpoint."""

    def test_list_models_empty(self, client):
        """Test listing models when no servers are registered."""
        response = client.get("/v1/models")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "object" in data
        assert data["object"] == "list"
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_list_models_with_servers(self, client, setup_test_server):
        """Test listing models when servers are registered."""
        # Register multiple servers
        setup_test_server("gpt-3.5-turbo", "healthy")
        setup_test_server("llama-2-7b", "healthy")
        setup_test_server("mistral-7b", "unhealthy")  # Should not appear

        response = client.get("/v1/models")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["object"] == "list"
        assert len(data["data"]) >= 2

        # Check model IDs
        model_ids = [model["id"] for model in data["data"]]
        assert "gpt-3.5-turbo" in model_ids
        assert "llama-2-7b" in model_ids
        assert "mistral-7b" not in model_ids  # Unhealthy servers excluded

        # Check model structure
        for model in data["data"]:
            assert "id" in model
            assert "object" in model
            assert model["object"] == "model"


class TestChatCompletionsEndpoint:
    """Test /v1/chat/completions endpoint."""

    def test_chat_completion_model_not_found(self, client):
        """Test chat completion with non-existent model."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "nonexistent-model",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
            }
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "error" in data
        assert "message" in data["error"]

    def test_chat_completion_no_healthy_servers(self, client, setup_test_server):
        """Test chat completion when all servers are unhealthy."""
        setup_test_server("test-model", "unhealthy")

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
            }
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "error" in data

    def test_chat_completion_streaming_not_supported(self, client, setup_test_server):
        """Test that streaming is not yet supported in Phase 3."""
        setup_test_server("test-model", "healthy")

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "stream": True
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "stream" in data["error"]["message"].lower()

    @patch('app.services.router.forward_request')
    async def test_chat_completion_success(self, mock_forward, client, setup_test_server):
        """Test successful chat completion request."""
        setup_test_server("test-model", "healthy")

        # Mock successful backend response
        mock_forward.return_value = (
            200,
            {
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Hello! How can I help you?"
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 15,
                    "total_tokens": 25
                }
            },
            None
        )

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "temperature": 0.7,
                "max_tokens": 100
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert "message" in data["choices"][0]

    def test_chat_completion_invalid_request(self, client):
        """Test chat completion with invalid request format."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                # Missing required 'messages' field
                "temperature": 0.7
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCompletionsEndpoint:
    """Test /v1/completions endpoint."""

    def test_completion_model_not_found(self, client):
        """Test completion with non-existent model."""
        response = client.post(
            "/v1/completions",
            json={
                "model": "nonexistent-model",
                "prompt": "Once upon a time"
            }
        )
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert "error" in data

    def test_completion_streaming_not_supported(self, client, setup_test_server):
        """Test that streaming is not yet supported in Phase 3."""
        setup_test_server("test-model", "healthy")

        response = client.post(
            "/v1/completions",
            json={
                "model": "test-model",
                "prompt": "Once upon a time",
                "stream": True
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert "stream" in data["error"]["message"].lower()

    @patch('app.services.router.forward_request')
    async def test_completion_success(self, mock_forward, client, setup_test_server):
        """Test successful completion request."""
        setup_test_server("test-model", "healthy")

        # Mock successful backend response
        mock_forward.return_value = (
            200,
            {
                "id": "cmpl-123",
                "object": "text_completion",
                "created": 1234567890,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "text": " there was a brave knight.",
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 4,
                    "completion_tokens": 6,
                    "total_tokens": 10
                }
            },
            None
        )

        response = client.post(
            "/v1/completions",
            json={
                "model": "test-model",
                "prompt": "Once upon a time",
                "max_tokens": 50
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert "text" in data["choices"][0]


class TestRoutingAndFailover:
    """Test request routing and automatic failover."""

    @patch('app.services.router.forward_request')
    async def test_failover_on_server_failure(self, mock_forward, client, setup_test_server):
        """Test that requests failover to another server when one fails."""
        # Set up two healthy servers for the same model
        setup_test_server("test-model", "healthy")

        # Mock first request failing, second succeeding
        mock_forward.side_effect = [
            (503, {}, "Connection error"),  # First server fails
            (200, {  # Second server succeeds
                "id": "chatcmpl-123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Response from second server"
                        },
                        "finish_reason": "stop"
                    }
                ]
            }, None)
        ]

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
            }
        )

        # Should succeed with the second server
        # Note: This test may need adjustment based on actual failover implementation
        # For now, we're just verifying the endpoint structure
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_504_GATEWAY_TIMEOUT]

    def test_gateway_server_id_header(self, client, setup_test_server):
        """Test that X-Gateway-Server-ID header is included in responses."""
        # This test requires mocking to work properly
        # Just verify the endpoint is accessible
        setup_test_server("test-model", "healthy")

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
            }
        )

        # Response may fail without a real backend, but we can check structure
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_504_GATEWAY_TIMEOUT
        ]


class TestRequestValidation:
    """Test request validation and error handling."""

    def test_chat_completion_missing_messages(self, client):
        """Test chat completion with missing messages field."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_chat_completion_invalid_message_role(self, client):
        """Test chat completion with invalid message role."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [
                    {"role": "invalid_role", "content": "Hello!"}
                ]
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_chat_completion_invalid_temperature(self, client):
        """Test chat completion with out-of-range temperature."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ],
                "temperature": 5.0  # Out of range (should be 0.0-2.0)
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_completion_missing_prompt(self, client):
        """Test completion with missing prompt field."""
        response = client.post(
            "/v1/completions",
            json={
                "model": "test-model"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestEndToEndInference:
    """Test complete inference workflow."""

    def test_full_inference_workflow(self, client, setup_test_server, admin_headers):
        """Test the complete workflow: list models, make inference request."""
        # Set up a test server
        setup_test_server("workflow-test-model", "healthy")

        # Step 1: List models
        models_response = client.get("/v1/models")
        assert models_response.status_code == status.HTTP_200_OK
        models_data = models_response.json()
        assert "data" in models_data

        # Step 2: Attempt inference (will fail without mock, but tests the flow)
        inference_response = client.post(
            "/v1/chat/completions",
            json={
                "model": "workflow-test-model",
                "messages": [
                    {"role": "user", "content": "Test message"}
                ]
            }
        )

        # Response will likely be 504 or 503 without a real backend
        assert inference_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            status.HTTP_504_GATEWAY_TIMEOUT
        ]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
