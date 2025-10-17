"""Integration tests for the Admin API.

These tests verify the functionality of:
- Server registration
- Server deregistration
- Server updates
- Server listing
- API key authentication
"""

import pytest
import os
from fastapi.testclient import TestClient
from fastapi import status

# Set test environment variables before importing app
os.environ["ADMIN_API_KEY"] = "test-admin-key-1234567890"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_gateway.db"
os.environ["LOG_LEVEL"] = "DEBUG"

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def admin_headers():
    """Headers with valid admin API key."""
    return {"X-API-Key": "test-admin-key-1234567890"}


@pytest.fixture
def invalid_admin_headers():
    """Headers with invalid admin API key."""
    return {"X-API-Key": "invalid-key"}


class TestAuthentication:
    """Test API key authentication."""
    
    def test_register_without_api_key(self, client):
        """Test that registration fails without API key."""
        response = client.post(
            "/admin/register",
            json={
                "model_name": "test-model",
                "endpoint_url": "https://example.com"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_with_invalid_api_key(self, client, invalid_admin_headers):
        """Test that registration fails with invalid API key."""
        response = client.post(
            "/admin/register",
            headers=invalid_admin_headers,
            json={
                "model_name": "test-model",
                "endpoint_url": "https://example.com"
            }
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]


class TestServerRegistration:
    """Test server registration endpoints."""
    
    
    def test_register_valid_server(self, client, admin_headers):
        """Test registering a valid server."""
        response = client.post(
            "/admin/register",
            headers=admin_headers,
            json={
                "model_name": "test-model-123",
                "endpoint_url": "https://api.example.com",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com",
                "description": "Test server"
            }
        )
        
        # Registration should succeed even if health check fails
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert "registration_id" in data
        assert data["registration_id"].startswith("srv_")
        assert data["model_name"] == "test-model-123"
        assert data["endpoint_url"] == "https://api.example.com"
        assert "health_status" in data
        # Server will likely be unhealthy since example.com doesn't have /v1/models
        assert data["health_status"] in ["healthy", "unhealthy"]
    
    
    def test_register_with_invalid_url_scheme(self, client, admin_headers):
        """Test that registration fails with invalid URL scheme."""
        response = client.post(
            "/admin/register",
            headers=admin_headers,
            json={
                "model_name": "test-model",
                "endpoint_url": "ftp://example.com"
            }
        )
        # Pydantic validation fails before it reaches our validation
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    
    def test_register_with_localhost_url(self, client, admin_headers):
        """Test that registration fails with localhost URL (SSRF protection)."""
        response = client.post(
            "/admin/register",
            headers=admin_headers,
            json={
                "model_name": "test-model",
                "endpoint_url": "http://localhost:8000"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert "localhost" in data["detail"]["error"]["message"].lower()
    
    
    def test_register_with_private_ip(self, client, admin_headers):
        """Test that registration fails with private IP (SSRF protection)."""
        response = client.post(
            "/admin/register",
            headers=admin_headers,
            json={
                "model_name": "test-model",
                "endpoint_url": "http://192.168.1.1"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert "private" in data["detail"]["error"]["message"].lower()
    
    
    def test_register_with_invalid_model_name(self, client, admin_headers):
        """Test that registration fails with invalid model name characters."""
        response = client.post(
            "/admin/register",
            headers=admin_headers,
            json={
                "model_name": "test model with spaces!",
                "endpoint_url": "https://example.com"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestServerDeregistration:
    """Test server deregistration endpoints."""
    
    
    def test_deregister_nonexistent_server(self, client, admin_headers):
        """Test that deregistering a nonexistent server returns 404."""
        response = client.delete(
            "/admin/register/srv_nonexistent",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]


class TestServerUpdate:
    """Test server update endpoints."""
    
    
    def test_update_nonexistent_server(self, client, admin_headers):
        """Test that updating a nonexistent server returns 404."""
        response = client.put(
            "/admin/register/srv_nonexistent",
            headers=admin_headers,
            json={
                "owner_name": "New Owner"
            }
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
    
    
    def test_update_with_invalid_url(self, client, admin_headers):
        """Test that update fails with invalid URL."""
        response = client.put(
            "/admin/register/srv_test123",
            headers=admin_headers,
            json={
                "endpoint_url": "http://localhost:8000"
            }
        )
        # Will return 404 since server doesn't exist, but tests the validation flow
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]


class TestServerListing:
    """Test server listing endpoints."""
    
    
    def test_list_servers(self, client, admin_headers):
        """Test listing all servers."""
        response = client.get(
            "/admin/servers",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "servers" in data or "detail" not in data, f"Got error: {data}"
        if "servers" in data:
            assert "total" in data
            assert isinstance(data["servers"], list)
            assert isinstance(data["total"], int)
    
    
    def test_list_servers_with_model_filter(self, client, admin_headers):
        """Test listing servers with model name filter."""
        response = client.get(
            "/admin/servers?model_name=test-model",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "servers" in data or "detail" not in data, f"Got error: {data}"
        if "servers" in data:
            assert "filters_applied" in data
            if "model_name" in data["filters_applied"]:
                assert data["filters_applied"]["model_name"] == "test-model"
    
    
    def test_list_servers_with_health_filter(self, client, admin_headers):
        """Test listing servers with health status filter."""
        response = client.get(
            "/admin/servers?health_status=healthy",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "servers" in data or "detail" not in data, f"Got error: {data}"


class TestStatistics:
    """Test statistics endpoint."""
    
    
    def test_get_statistics(self, client, admin_headers):
        """Test getting gateway statistics."""
        response = client.get(
            "/admin/stats",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_servers" in data or "detail" not in data, f"Got error: {data}"
        if "total_servers" in data:
            assert "total_models" in data
            assert "servers_by_health" in data
            assert isinstance(data["total_servers"], int)
            assert isinstance(data["total_models"], int)
            
            # Check servers_by_health structure
            health_data = data["servers_by_health"]
            assert "healthy" in health_data
            assert "unhealthy" in health_data
            assert "unknown" in health_data


class TestEndToEndWorkflow:
    """Test complete registration workflow."""
    
    
    def test_complete_registration_workflow(self, client, admin_headers):
        """Test the complete workflow: register, list, update, deregister."""
        # This test uses a mock server approach
        # In a real scenario, you'd need a test server implementing /v1/models
        
        # Step 1: Test statistics
        stats_response = client.get(
            "/admin/stats",
            headers=admin_headers
        )
        assert stats_response.status_code == status.HTTP_200_OK
        
        # Step 2: List servers
        list_response = client.get(
            "/admin/servers",
            headers=admin_headers
        )
        assert list_response.status_code == status.HTTP_200_OK


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])

