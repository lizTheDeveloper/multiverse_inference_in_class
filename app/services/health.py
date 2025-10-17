"""Health checking service for model servers.

This module provides functions to check the health of registered model servers
by making requests to their /v1/models endpoint and validating responses.
"""

import time
from typing import Tuple, Optional
import httpx

from app.utils.config import get_settings
from app.utils.logger import get_logger
from app.utils.models import HealthCheckResult

logger = get_logger(__name__)
settings = get_settings()


async def check_server_health(
    server_id: int,
    registration_id: str,
    endpoint_url: str,
    api_key: Optional[str] = None,
    timeout_seconds: Optional[int] = None
) -> HealthCheckResult:
    """Perform a health check on a single server.
    
    The health check sends a GET request to the server's /v1/models endpoint
    and validates that:
    1. The server responds within the timeout period
    2. The response status code is 200
    3. The response contains valid JSON
    
    Args:
        server_id: Database ID of the server
        registration_id: Registration ID of the server
        endpoint_url: Base URL of the server (e.g., "https://example.com")
        api_key: Optional API key for the backend server
        timeout_seconds: Request timeout in seconds (uses config default if None)
    
    Returns:
        HealthCheckResult with check outcome and details
    """
    if timeout_seconds is None:
        timeout_seconds = settings.health_check_timeout_seconds
    
    # Construct the health check URL
    health_check_url = f"{endpoint_url.rstrip('/')}/v1/models"
    
    logger.debug(
        f"Checking health of server {registration_id} at {health_check_url}"
    )
    
    start_time = time.time()
    
    try:
        # Prepare headers
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # Make the request
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(health_check_url, headers=headers)
        
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        # Check if response is successful
        if response.status_code == 200:
            # Try to parse JSON to ensure it's valid
            try:
                response_json = response.json()
                
                # Validate that response has expected structure
                # OpenAI /v1/models returns {"object": "list", "data": [...]}
                if not isinstance(response_json, dict):
                    raise ValueError("Response is not a JSON object")
                
                logger.info(
                    f"Server {registration_id} is healthy "
                    f"(response time: {response_time_ms}ms)"
                )
                
                return HealthCheckResult(
                    server_id=server_id,
                    registration_id=registration_id,
                    endpoint_url=endpoint_url,
                    is_healthy=True,
                    response_time_ms=response_time_ms,
                    error_message=None,
                    checked_at=time.strftime("%Y-%m-%dT%H:%M:%S")
                )
                
            except Exception as json_error:
                logger.warning(
                    f"Server {registration_id} returned 200 but invalid JSON: {json_error}"
                )
                return HealthCheckResult(
                    server_id=server_id,
                    registration_id=registration_id,
                    endpoint_url=endpoint_url,
                    is_healthy=False,
                    response_time_ms=response_time_ms,
                    error_message=f"Invalid JSON response: {str(json_error)}",
                    checked_at=time.strftime("%Y-%m-%dT%H:%M:%S")
                )
        else:
            logger.warning(
                f"Server {registration_id} returned status code {response.status_code}"
            )
            return HealthCheckResult(
                server_id=server_id,
                registration_id=registration_id,
                endpoint_url=endpoint_url,
                is_healthy=False,
                response_time_ms=response_time_ms,
                error_message=f"HTTP {response.status_code}: {response.text[:200]}",
                checked_at=time.strftime("%Y-%m-%dT%H:%M:%S")
            )
    
    except httpx.TimeoutException:
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        logger.warning(
            f"Server {registration_id} health check timed out after {timeout_seconds}s"
        )
        return HealthCheckResult(
            server_id=server_id,
            registration_id=registration_id,
            endpoint_url=endpoint_url,
            is_healthy=False,
            response_time_ms=response_time_ms,
            error_message=f"Request timed out after {timeout_seconds} seconds",
            checked_at=time.strftime("%Y-%m-%dT%H:%M:%S")
        )
    
    except httpx.RequestError as request_error:
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        logger.warning(
            f"Server {registration_id} health check failed: {request_error}"
        )
        return HealthCheckResult(
            server_id=server_id,
            registration_id=registration_id,
            endpoint_url=endpoint_url,
            is_healthy=False,
            response_time_ms=response_time_ms,
            error_message=f"Request error: {str(request_error)}",
            checked_at=time.strftime("%Y-%m-%dT%H:%M:%S")
        )
    
    except Exception as error:
        end_time = time.time()
        response_time_ms = int((end_time - start_time) * 1000)
        
        logger.error(
            f"Unexpected error checking server {registration_id}: {error}",
            exc_info=True
        )
        return HealthCheckResult(
            server_id=server_id,
            registration_id=registration_id,
            endpoint_url=endpoint_url,
            is_healthy=False,
            response_time_ms=response_time_ms,
            error_message=f"Unexpected error: {str(error)}",
            checked_at=time.strftime("%Y-%m-%dT%H:%M:%S")
        )


async def perform_initial_health_check(
    server_id: int,
    registration_id: str,
    endpoint_url: str,
    api_key: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Perform initial health check during registration.
    
    This is a simplified version that just returns success/failure
    without storing the full result.
    
    Args:
        server_id: Database ID of the server
        registration_id: Registration ID of the server
        endpoint_url: Base URL of the server
        api_key: Optional API key for the backend server
    
    Returns:
        Tuple of (is_healthy, error_message)
    """
    logger.info(f"Performing initial health check for server {registration_id}")
    
    result = await check_server_health(
        server_id=server_id,
        registration_id=registration_id,
        endpoint_url=endpoint_url,
        api_key=api_key
    )
    
    if result.is_healthy:
        logger.info(
            f"Initial health check passed for server {registration_id} "
            f"(response time: {result.response_time_ms}ms)"
        )
        return True, None
    else:
        logger.warning(
            f"Initial health check failed for server {registration_id}: "
            f"{result.error_message}"
        )
        return False, result.error_message


if __name__ == "__main__":
    # Test health check functionality
    import asyncio
    import os
    
    os.environ["ADMIN_API_KEY"] = "test-key-1234567890"
    
    async def test_health_check():
        """Test health check with a known endpoint."""
        # Test with a public API (httpbin)
        result = await check_server_health(
            server_id=1,
            registration_id="test-123",
            endpoint_url="https://httpbin.org",
            api_key=None,
            timeout_seconds=10
        )
        
        print(f"Health check result:")
        print(f"  Healthy: {result.is_healthy}")
        print(f"  Response time: {result.response_time_ms}ms")
        print(f"  Error: {result.error_message}")
        print(f"  Checked at: {result.checked_at}")
    
    asyncio.run(test_health_check())

