"""Registry service for managing model server registrations.

This module provides CRUD operations for the model_servers table and handles
all database interactions related to server registration and management.
"""

import secrets
from datetime import datetime
from typing import List, Optional, Dict, Any
import aiosqlite

from app.utils.config import get_settings
from app.utils.database import get_db_connection, get_timestamp
from app.utils.logger import get_logger
from app.utils.models import ServerListItem

logger = get_logger(__name__)
settings = get_settings()


def generate_registration_id() -> str:
    """Generate a unique registration ID for a new server.
    
    Returns:
        A unique registration ID in format 'srv_<random_hex>'
    """
    # Generate a 16-character random hex string
    random_hex = secrets.token_hex(8)
    return f"srv_{random_hex}"


async def register_server(
    model_name: str,
    endpoint_url: str,
    api_key: Optional[str] = None,
    owner_name: Optional[str] = None,
    owner_email: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    initial_health_status: str = "unknown"
) -> Dict[str, Any]:
    """Register a new model server in the database.
    
    Args:
        model_name: Name of the model being served
        endpoint_url: URL of the model server
        api_key: Optional API key for the backend server
        owner_name: Optional name of the server owner
        owner_email: Optional email of the server owner
        description: Optional description of the server
        tags: Optional comma-separated tags
        initial_health_status: Initial health status (default: "unknown")
    
    Returns:
        Dictionary containing the registered server information
    
    Raises:
        Exception: If database operation fails
    """
    registration_id = generate_registration_id()
    timestamp = get_timestamp()
    
    logger.info(
        f"Registering new server: {registration_id} "
        f"(model: {model_name}, url: {endpoint_url})"
    )
    
    try:
        connection = await get_db_connection()
        
        try:
            # Insert the new server
            cursor = await connection.execute(
                """
                INSERT INTO model_servers (
                    registration_id, model_name, endpoint_url, api_key,
                    owner_name, owner_email, description, tags,
                    health_status, consecutive_failures, is_active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
                """,
                (
                    registration_id, model_name, endpoint_url, api_key,
                    owner_name, owner_email, description, tags,
                    initial_health_status, timestamp, timestamp
                )
            )
            
            server_id = cursor.lastrowid
            await connection.commit()
            
            logger.info(
                f"Server registered successfully: {registration_id} (id: {server_id})"
            )
            
            return {
                "id": server_id,
                "registration_id": registration_id,
                "model_name": model_name,
                "endpoint_url": endpoint_url,
                "owner_name": owner_name,
                "owner_email": owner_email,
                "health_status": initial_health_status,
                "created_at": timestamp
            }
        
        finally:
            await connection.close()
    
    except Exception as error:
        logger.error(f"Failed to register server: {error}", exc_info=True)
        raise


async def deregister_server(registration_id: str) -> bool:
    """Deregister a server (soft delete by setting is_active = 0).
    
    Args:
        registration_id: Registration ID of the server to deregister
    
    Returns:
        True if server was deregistered, False if not found
    
    Raises:
        Exception: If database operation fails
    """
    logger.info(f"Deregistering server: {registration_id}")
    
    try:
        connection = await get_db_connection()
        
        try:
            # Soft delete by setting is_active = 0
            cursor = await connection.execute(
                """
                UPDATE model_servers
                SET is_active = 0, updated_at = ?
                WHERE registration_id = ? AND is_active = 1
                """,
                (get_timestamp(), registration_id)
            )
            
            await connection.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Server deregistered successfully: {registration_id}")
                return True
            else:
                logger.warning(f"Server not found or already deregistered: {registration_id}")
                return False
        
        finally:
            await connection.close()
    
    except Exception as error:
        logger.error(f"Failed to deregister server: {error}", exc_info=True)
        raise


async def update_server(
    registration_id: str,
    model_name: Optional[str] = None,
    endpoint_url: Optional[str] = None,
    api_key: Optional[str] = None,
    owner_name: Optional[str] = None,
    owner_email: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None
) -> bool:
    """Update server details.
    
    Args:
        registration_id: Registration ID of the server to update
        model_name: New model name (if provided)
        endpoint_url: New endpoint URL (if provided)
        api_key: New API key (if provided, use empty string to clear)
        owner_name: New owner name (if provided)
        owner_email: New owner email (if provided)
        description: New description (if provided)
        tags: New tags (if provided)
    
    Returns:
        True if server was updated, False if not found
    
    Raises:
        Exception: If database operation fails
    """
    logger.info(f"Updating server: {registration_id}")
    
    # Build dynamic UPDATE query based on provided fields
    update_fields = []
    params = []
    
    if model_name is not None:
        update_fields.append("model_name = ?")
        params.append(model_name)
    
    if endpoint_url is not None:
        update_fields.append("endpoint_url = ?")
        params.append(endpoint_url)
    
    if api_key is not None:
        update_fields.append("api_key = ?")
        params.append(api_key if api_key else None)  # Empty string becomes NULL
    
    if owner_name is not None:
        update_fields.append("owner_name = ?")
        params.append(owner_name)
    
    if owner_email is not None:
        update_fields.append("owner_email = ?")
        params.append(owner_email)
    
    if description is not None:
        update_fields.append("description = ?")
        params.append(description)
    
    if tags is not None:
        update_fields.append("tags = ?")
        params.append(tags)
    
    if not update_fields:
        logger.warning(f"No fields to update for server: {registration_id}")
        return False
    
    # Always update the updated_at timestamp
    update_fields.append("updated_at = ?")
    params.append(get_timestamp())
    
    # Add registration_id to params for WHERE clause
    params.append(registration_id)
    
    try:
        connection = await get_db_connection()
        
        try:
            query = f"""
                UPDATE model_servers
                SET {', '.join(update_fields)}
                WHERE registration_id = ? AND is_active = 1
            """
            
            cursor = await connection.execute(query, params)
            await connection.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Server updated successfully: {registration_id}")
                return True
            else:
                logger.warning(f"Server not found: {registration_id}")
                return False
        
        finally:
            await connection.close()
    
    except Exception as error:
        logger.error(f"Failed to update server: {error}", exc_info=True)
        raise


async def get_server_by_id(server_id: int) -> Optional[Dict[str, Any]]:
    """Get server details by database ID.
    
    Args:
        server_id: Database ID of the server
    
    Returns:
        Dictionary with server details, or None if not found
    """
    try:
        connection = await get_db_connection()
        
        try:
            cursor = await connection.execute(
                """
                SELECT * FROM model_servers
                WHERE id = ? AND is_active = 1
                """,
                (server_id,)
            )
            
            row = await cursor.fetchone()
            
            if row:
                # Convert Row to dictionary
                return dict(row)
            else:
                return None
        
        finally:
            await connection.close()
    
    except Exception as error:
        logger.error(f"Failed to get server by ID {server_id}: {error}", exc_info=True)
        raise


async def get_server_by_registration_id(registration_id: str) -> Optional[Dict[str, Any]]:
    """Get server details by registration ID.
    
    Args:
        registration_id: Registration ID of the server
    
    Returns:
        Dictionary with server details, or None if not found
    """
    try:
        connection = await get_db_connection()
        
        try:
            cursor = await connection.execute(
                """
                SELECT * FROM model_servers
                WHERE registration_id = ? AND is_active = 1
                """,
                (registration_id,)
            )
            
            row = await cursor.fetchone()
            
            if row:
                return dict(row)
            else:
                return None
        
        finally:
            await connection.close()
    
    except Exception as error:
        logger.error(
            f"Failed to get server by registration ID {registration_id}: {error}",
            exc_info=True
        )
        raise


async def list_servers(
    model_name: Optional[str] = None,
    health_status: Optional[str] = None,
    include_inactive: bool = False
) -> List[ServerListItem]:
    """List all registered servers with optional filtering.
    
    Args:
        model_name: Filter by model name (if provided)
        health_status: Filter by health status (if provided)
        include_inactive: Whether to include inactive servers
    
    Returns:
        List of ServerListItem objects
    """
    logger.debug(
        f"Listing servers (model: {model_name}, status: {health_status}, "
        f"include_inactive: {include_inactive})"
    )
    
    try:
        connection = await get_db_connection()
        
        try:
            # Build query with filters
            query = "SELECT * FROM model_servers WHERE 1=1"
            params = []
            
            if not include_inactive:
                query += " AND is_active = 1"
            
            if model_name:
                query += " AND model_name = ?"
                params.append(model_name)
            
            if health_status:
                query += " AND health_status = ?"
                params.append(health_status)
            
            # Order by created_at descending (newest first)
            query += " ORDER BY created_at DESC"
            
            cursor = await connection.execute(query, params)
            rows = await cursor.fetchall()
            
            # Convert rows to ServerListItem objects
            servers = []
            for row in rows:
                row_dict = dict(row)
                # Convert integer boolean to Python boolean
                row_dict["is_active"] = bool(row_dict["is_active"])
                servers.append(ServerListItem(**row_dict))
            
            logger.debug(f"Found {len(servers)} servers matching criteria")
            return servers
        
        finally:
            await connection.close()
    
    except Exception as error:
        logger.error(f"Failed to list servers: {error}", exc_info=True)
        raise


async def find_healthy_servers(model_name: str) -> List[Dict[str, Any]]:
    """Find all healthy servers for a specific model.
    
    This is used by the routing service to find available servers.
    
    Args:
        model_name: Name of the model to search for
    
    Returns:
        List of dictionaries with server details
    """
    logger.debug(f"Finding healthy servers for model: {model_name}")
    
    try:
        connection = await get_db_connection()
        
        try:
            cursor = await connection.execute(
                """
                SELECT * FROM model_servers
                WHERE model_name = ?
                  AND health_status = 'healthy'
                  AND is_active = 1
                ORDER BY last_successful_request_at DESC NULLS LAST,
                         consecutive_failures ASC
                """,
                (model_name,)
            )
            
            rows = await cursor.fetchall()
            servers = [dict(row) for row in rows]
            
            logger.debug(f"Found {len(servers)} healthy servers for model {model_name}")
            return servers
        
        finally:
            await connection.close()
    
    except Exception as error:
        logger.error(
            f"Failed to find healthy servers for {model_name}: {error}",
            exc_info=True
        )
        raise


async def update_health_status(
    server_id: int,
    is_healthy: bool,
    error_message: Optional[str] = None
) -> None:
    """Update the health status of a server.
    
    Args:
        server_id: Database ID of the server
        is_healthy: Whether the server is healthy
        error_message: Optional error message if unhealthy
    """
    timestamp = get_timestamp()
    
    try:
        connection = await get_db_connection()
        
        try:
            if is_healthy:
                # Server is healthy - reset consecutive failures
                await connection.execute(
                    """
                    UPDATE model_servers
                    SET health_status = 'healthy',
                        consecutive_failures = 0,
                        last_checked_at = ?,
                        last_successful_request_at = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (timestamp, timestamp, timestamp, server_id)
                )
            else:
                # Server is unhealthy - increment consecutive failures
                await connection.execute(
                    """
                    UPDATE model_servers
                    SET health_status = 'unhealthy',
                        consecutive_failures = consecutive_failures + 1,
                        last_checked_at = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (timestamp, timestamp, server_id)
                )
            
            await connection.commit()
            
            logger.debug(
                f"Updated health status for server {server_id}: "
                f"{'healthy' if is_healthy else 'unhealthy'}"
            )
        
        finally:
            await connection.close()
    
    except Exception as error:
        logger.error(
            f"Failed to update health status for server {server_id}: {error}",
            exc_info=True
        )
        raise


async def get_server_count() -> int:
    """Get total count of active servers.
    
    Returns:
        Number of active servers
    """
    try:
        connection = await get_db_connection()
        
        try:
            cursor = await connection.execute(
                "SELECT COUNT(*) FROM model_servers WHERE is_active = 1"
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
        
        finally:
            await connection.close()
    
    except Exception as error:
        logger.error(f"Failed to get server count: {error}", exc_info=True)
        raise


async def get_model_count() -> int:
    """Get count of distinct models.
    
    Returns:
        Number of distinct models
    """
    try:
        connection = await get_db_connection()
        
        try:
            cursor = await connection.execute(
                "SELECT COUNT(DISTINCT model_name) FROM model_servers WHERE is_active = 1"
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
        
        finally:
            await connection.close()
    
    except Exception as error:
        logger.error(f"Failed to get model count: {error}", exc_info=True)
        raise

