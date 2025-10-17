"""Router service for handling inference request routing and load balancing.

This module implements the core routing logic for directing inference requests
to healthy backend servers with round-robin load balancing and automatic failover.
Supports both regular and streaming responses.
"""

import time
import httpx
import json
from typing import Optional, Dict, Any, Tuple, AsyncGenerator
from threading import Lock

from app.utils.logger import get_logger
from app.utils.database import get_db_connection
from app.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class RoundRobinLoadBalancer:
    """Round-robin load balancer for distributing requests across healthy servers.

    This class maintains a counter for each model to ensure even distribution
    of requests across all healthy servers hosting that model.
    """

    def __init__(self):
        """Initialize the load balancer with empty counters."""
        self._counters: Dict[str, int] = {}
        self._lock = Lock()

    def select_server(self, model_name: str, healthy_servers: list) -> Optional[dict]:
        """Select a server using round-robin algorithm.

        Args:
            model_name: Name of the model being requested
            healthy_servers: List of healthy server dictionaries

        Returns:
            Selected server dictionary or None if no servers available
        """
        if not healthy_servers:
            logger.warning(f"No healthy servers available for model: {model_name}")
            return None

        with self._lock:
            # Initialize counter for this model if it doesn't exist
            if model_name not in self._counters:
                self._counters[model_name] = 0

            # Select server using round-robin
            index = self._counters[model_name] % len(healthy_servers)
            selected_server = healthy_servers[index]

            # Increment counter for next request
            self._counters[model_name] = (self._counters[model_name] + 1) % len(healthy_servers)

            logger.debug(
                f"Round-robin selected server {selected_server['registration_id']} "
                f"for model {model_name} (index {index} of {len(healthy_servers)})"
            )

            return selected_server


# Global load balancer instance
_load_balancer = RoundRobinLoadBalancer()


async def get_healthy_servers(model_name: str) -> list:
    """Query the database for healthy servers hosting the specified model.

    Args:
        model_name: Name of the model to find servers for

    Returns:
        List of server dictionaries with all server details
    """
    conn = await get_db_connection()

    query = """
        SELECT
            id, registration_id, model_name, endpoint_url, api_key,
            owner_name, owner_email, health_status, consecutive_failures,
            last_checked_at, last_successful_request_at, is_active,
            created_at, updated_at, description, tags
        FROM model_servers
        WHERE model_name = ?
            AND health_status = 'healthy'
            AND is_active = 1
        ORDER BY last_successful_request_at ASC NULLS FIRST
    """

    cursor = await conn.execute(query, (model_name,))
    rows = await cursor.fetchall()

    await conn.close()

    # Convert Row objects to dictionaries
    servers = [dict(row) for row in rows]

    logger.info(
        f"Found {len(servers)} healthy server(s) for model '{model_name}'"
    )

    return servers


async def update_server_last_successful_request(server_id: int) -> None:
    """Update the last successful request timestamp for a server.

    Args:
        server_id: Database ID of the server
    """
    conn = await get_db_connection()

    await conn.execute(
        """
        UPDATE model_servers
        SET last_successful_request_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (server_id,)
    )

    await conn.commit()
    await conn.close()


async def mark_server_unhealthy(server_id: int, reason: str) -> None:
    """Mark a server as unhealthy and increment consecutive failures.

    Args:
        server_id: Database ID of the server
        reason: Reason why the server is being marked unhealthy
    """
    conn = await get_db_connection()

    await conn.execute(
        """
        UPDATE model_servers
        SET
            health_status = 'unhealthy',
            consecutive_failures = consecutive_failures + 1,
            last_checked_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (server_id,)
    )

    await conn.commit()
    await conn.close()

    logger.warning(
        f"Marked server {server_id} as unhealthy. Reason: {reason}"
    )


async def forward_request(
    server: dict,
    endpoint: str,
    request_data: dict,
    timeout: int = 300
) -> Tuple[int, Dict[Any, Any], Optional[str]]:
    """Forward an inference request to a backend server.

    Args:
        server: Server dictionary containing endpoint_url and api_key
        endpoint: API endpoint path (e.g., '/v1/chat/completions')
        request_data: Request body as dictionary
        timeout: Request timeout in seconds (default: 300)

    Returns:
        Tuple of (status_code, response_dict, error_message)

    Raises:
        Exception: If request fails after all retries
    """
    url = f"{server['endpoint_url']}{endpoint}"
    headers = {}

    # Add backend server's API key if configured
    if server.get('api_key'):
        headers['Authorization'] = f"Bearer {server['api_key']}"

    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.debug(f"Forwarding request to {url}")

            response = await client.post(
                url,
                json=request_data,
                headers=headers
            )

            elapsed_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Backend server {server['registration_id']} responded: "
                f"status={response.status_code}, latency={elapsed_ms}ms"
            )

            # Parse response
            try:
                response_data = response.json()
            except Exception:
                response_data = {"text": response.text}

            return response.status_code, response_data, None

    except httpx.TimeoutException as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Request timeout after {elapsed_ms}ms"
        logger.error(
            f"Timeout forwarding request to {url}: {error_msg}"
        )
        return 504, {}, error_msg

    except httpx.RequestError as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Request error: {str(exc)}"
        logger.error(
            f"Error forwarding request to {url}: {error_msg}"
        )
        return 503, {}, error_msg

    except Exception as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Unexpected error: {str(exc)}"
        logger.error(
            f"Unexpected error forwarding request to {url}: {error_msg}",
            exc_info=True
        )
        return 500, {}, error_msg


async def forward_streaming_request(
    server: dict,
    endpoint: str,
    request_data: dict,
    timeout: int = 300
) -> AsyncGenerator[str, None]:
    """Forward a streaming inference request to a backend server.
    
    This function handles Server-Sent Events (SSE) streaming by forwarding
    the request to the backend and yielding chunks as they arrive.
    
    Args:
        server: Server dictionary containing endpoint_url and api_key
        endpoint: API endpoint path (e.g., '/v1/chat/completions')
        request_data: Request body as dictionary
        timeout: Request timeout in seconds (default: 300)
        
    Yields:
        SSE-formatted strings (data: {json}\\n\\n)
        
    Raises:
        Exception: If streaming fails or connection is lost
    """
    url = f"{server['endpoint_url']}{endpoint}"
    headers = {}
    
    # Add backend server's API key if configured
    if server.get('api_key'):
        headers['Authorization'] = f"Bearer {server['api_key']}"
    
    start_time = time.time()
    chunk_count = 0
    total_bytes = 0
    
    logger.info(
        f"Starting streaming request to {server['registration_id']} at {url}",
        extra={"server_id": server['registration_id'], "endpoint": endpoint}
    )
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                'POST',
                url,
                json=request_data,
                headers=headers
            ) as response:
                
                # Check if response status is OK
                if response.status_code != 200:
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    error_msg = f"Backend returned status {response.status_code}"
                    logger.error(
                        f"Streaming request to {server['registration_id']} failed: "
                        f"status={response.status_code}, latency={elapsed_ms}ms"
                    )
                    
                    # Try to read error response
                    try:
                        error_body = await response.aread()
                        logger.error(f"Error body: {error_body.decode()}")
                    except Exception:
                        pass
                    
                    raise Exception(error_msg)
                
                # Stream chunks from backend to client
                async for chunk in response.aiter_bytes():
                    if chunk:
                        chunk_count += 1
                        total_bytes += len(chunk)
                        
                        # Decode and yield the chunk
                        decoded_chunk = chunk.decode('utf-8')
                        yield decoded_chunk
                
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                logger.info(
                    f"Streaming request to {server['registration_id']} completed: "
                    f"chunks={chunk_count}, bytes={total_bytes}, latency={elapsed_ms}ms",
                    extra={
                        "server_id": server['registration_id'],
                        "chunk_count": chunk_count,
                        "total_bytes": total_bytes,
                        "latency_ms": elapsed_ms
                    }
                )
                
    except httpx.TimeoutException as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Streaming timeout after {elapsed_ms}ms"
        logger.error(
            f"Timeout during streaming request to {url}: {error_msg}",
            extra={
                "server_id": server['registration_id'],
                "chunk_count": chunk_count,
                "total_bytes": total_bytes
            }
        )
        raise Exception(error_msg)
    
    except httpx.RequestError as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Request error: {str(exc)}"
        logger.error(
            f"Error during streaming request to {url}: {error_msg}",
            extra={
                "server_id": server['registration_id'],
                "chunk_count": chunk_count,
                "total_bytes": total_bytes
            }
        )
        raise Exception(error_msg)
    
    except Exception as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        error_msg = f"Unexpected error: {str(exc)}"
        logger.error(
            f"Unexpected error during streaming request to {url}: {error_msg}",
            exc_info=True,
            extra={
                "server_id": server['registration_id'],
                "chunk_count": chunk_count,
                "total_bytes": total_bytes
            }
        )
        raise Exception(error_msg)


async def handle_streaming_request(
    model_name: str,
    endpoint: str,
    request_data: dict
) -> Tuple[Optional[dict], Optional[AsyncGenerator[str, None]], Optional[str]]:
    """Handle a streaming inference request with server selection.
    
    This function finds a healthy server, selects one using round-robin,
    and returns a streaming generator for the response.
    
    Args:
        model_name: Name of the model being requested
        endpoint: API endpoint path
        request_data: Request body as dictionary
        
    Returns:
        Tuple of (selected_server_dict, streaming_generator, error_message)
        If successful: (server, generator, None)
        If failed: (None, None, error_message)
    """
    logger.info(
        f"Handling streaming {endpoint} request for model '{model_name}'"
    )
    
    # Get healthy servers
    healthy_servers = await get_healthy_servers(model_name)
    
    if not healthy_servers:
        logger.error(f"No healthy servers available for model '{model_name}'")
        return None, None, "No healthy servers available for this model"
    
    # Select server using round-robin
    server = _load_balancer.select_server(model_name, healthy_servers)
    
    if not server:
        logger.error(f"Failed to select server for model '{model_name}'")
        return None, None, "Failed to select server"
    
    logger.info(
        f"Selected server {server['registration_id']} for streaming request"
    )
    
    try:
        # Create streaming generator
        stream_generator = forward_streaming_request(
            server,
            endpoint,
            request_data,
            timeout=settings.request_timeout_seconds
        )
        
        return server, stream_generator, None
        
    except Exception as exc:
        error_msg = str(exc)
        logger.error(
            f"Failed to create streaming request: {error_msg}",
            exc_info=True
        )
        
        # Mark server as unhealthy
        await mark_server_unhealthy(
            server['id'],
            f"Streaming request failed: {error_msg}"
        )
        
        return None, None, error_msg


async def handle_request(
    model_name: str,
    endpoint: str,
    request_data: dict,
    max_retries: int = 2
) -> Tuple[int, Dict[Any, Any], Optional[str], Optional[str]]:
    """Handle an inference request with automatic failover.

    This function implements the main routing logic:
    1. Find healthy servers for the requested model
    2. Select a server using round-robin
    3. Forward the request to the selected server
    4. If the request fails, mark server unhealthy and retry with another server
    5. Return response or error after all retries exhausted

    Args:
        model_name: Name of the model being requested
        endpoint: API endpoint path
        request_data: Request body as dictionary
        max_retries: Maximum number of retry attempts (default: 2)

    Returns:
        Tuple of (status_code, response_dict, error_message, server_id)
    """
    logger.info(
        f"Handling {endpoint} request for model '{model_name}'"
    )

    # Get healthy servers
    healthy_servers = await get_healthy_servers(model_name)

    if not healthy_servers:
        logger.error(f"No healthy servers available for model '{model_name}'")
        return 503, {}, "No healthy servers available for this model", None

    # Try up to max_retries servers
    attempts = 0
    last_error = None

    while attempts < max_retries and healthy_servers:
        attempts += 1

        # Select server using round-robin
        server = _load_balancer.select_server(model_name, healthy_servers)

        if not server:
            break

        logger.info(
            f"Attempt {attempts}/{max_retries}: Routing to server "
            f"{server['registration_id']} at {server['endpoint_url']}"
        )

        # Forward request
        status_code, response_data, error_msg = await forward_request(
            server,
            endpoint,
            request_data,
            timeout=settings.request_timeout_seconds
        )

        # Check if request was successful
        if status_code == 200:
            # Update last successful request timestamp
            await update_server_last_successful_request(server['id'])

            logger.info(
                f"Successfully routed request to server {server['registration_id']}"
            )

            return status_code, response_data, None, server['registration_id']

        # Request failed - mark server unhealthy and try next server
        last_error = error_msg or f"Backend returned status {status_code}"
        await mark_server_unhealthy(
            server['id'],
            f"Request failed: {last_error}"
        )

        # Remove failed server from list
        healthy_servers = [s for s in healthy_servers if s['id'] != server['id']]

        logger.warning(
            f"Request to server {server['registration_id']} failed: {last_error}. "
            f"{len(healthy_servers)} server(s) remaining for retry."
        )

    # All retries exhausted
    logger.error(
        f"All retry attempts exhausted for model '{model_name}'. "
        f"Last error: {last_error}"
    )

    return 504, {}, f"All servers failed. Last error: {last_error}", None
