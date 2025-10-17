"""Background health checker service for continuous server monitoring.

This module provides a background task that continuously monitors all registered
servers, updates their health status, and automatically deregisters servers that
fail consecutive health checks.
"""

import asyncio
from datetime import datetime
from typing import Optional

from app.utils.config import get_settings
from app.utils.logger import get_logger
from app.services.health import check_server_health
from app.services.registry import (
    list_servers,
    update_health_status,
    deregister_server,
    get_server_by_id
)

logger = get_logger(__name__)
settings = get_settings()

# Global flag to control the health checker loop
_health_checker_running = False
_health_checker_task: Optional[asyncio.Task] = None


async def check_all_servers() -> dict:
    """Perform health checks on all active servers.
    
    This function queries all active servers and checks their health status.
    It updates the database with the results and tracks consecutive failures.
    
    Returns:
        Dictionary with check statistics:
        - total_checked: Number of servers checked
        - healthy_count: Number of healthy servers
        - unhealthy_count: Number of unhealthy servers
        - deregistered_count: Number of servers auto-deregistered
        - check_duration_seconds: Time taken to check all servers
    """
    start_time = asyncio.get_event_loop().time()
    
    # Get all active servers
    servers = await list_servers(include_inactive=False)
    
    if not servers:
        logger.debug("No active servers to check")
        return {
            "total_checked": 0,
            "healthy_count": 0,
            "unhealthy_count": 0,
            "deregistered_count": 0,
            "check_duration_seconds": 0
        }
    
    logger.info(f"Starting health check cycle for {len(servers)} servers")
    
    healthy_count = 0
    unhealthy_count = 0
    deregistered_count = 0
    
    # Check each server
    for server in servers:
        server_id = server.id
        registration_id = server.registration_id
        endpoint_url = server.endpoint_url
        api_key = None  # We don't expose api_key in ServerListItem for security
        
        # Get full server details to access api_key
        server_details = await get_server_by_id(server_id)
        if server_details:
            api_key = server_details.get("api_key")
        
        # Perform health check
        result = await check_server_health(
            server_id=server_id,
            registration_id=registration_id,
            endpoint_url=endpoint_url,
            api_key=api_key
        )
        
        # Update database with result
        await update_health_status(
            server_id=server_id,
            is_healthy=result.is_healthy,
            error_message=result.error_message
        )
        
        if result.is_healthy:
            healthy_count += 1
            logger.debug(
                f"Server {registration_id} is healthy "
                f"(response time: {result.response_time_ms}ms)"
            )
        else:
            unhealthy_count += 1
            
            # Get updated server details to check consecutive failures
            updated_server = await get_server_by_id(server_id)
            if updated_server:
                consecutive_failures = updated_server.get("consecutive_failures", 0)
                
                logger.warning(
                    f"Server {registration_id} is unhealthy "
                    f"(consecutive failures: {consecutive_failures}) - "
                    f"{result.error_message}"
                )
                
                # Check if we should auto-deregister
                if (settings.auto_deregister_after_failures and
                    consecutive_failures >= settings.max_consecutive_failures):
                    
                    logger.error(
                        f"Server {registration_id} has failed "
                        f"{consecutive_failures} consecutive health checks. "
                        "Auto-deregistering."
                    )
                    
                    success = await deregister_server(registration_id)
                    if success:
                        deregistered_count += 1
                        logger.info(f"Server {registration_id} auto-deregistered")
                    else:
                        logger.error(
                            f"Failed to auto-deregister server {registration_id}"
                        )
    
    end_time = asyncio.get_event_loop().time()
    duration = end_time - start_time
    
    logger.info(
        f"Health check cycle complete: {len(servers)} servers checked, "
        f"{healthy_count} healthy, {unhealthy_count} unhealthy, "
        f"{deregistered_count} deregistered in {duration:.2f}s"
    )
    
    return {
        "total_checked": len(servers),
        "healthy_count": healthy_count,
        "unhealthy_count": unhealthy_count,
        "deregistered_count": deregistered_count,
        "check_duration_seconds": duration
    }


async def health_check_loop() -> None:
    """Main health checker loop that runs continuously.
    
    This function runs in the background and performs health checks
    at regular intervals defined by HEALTH_CHECK_INTERVAL_SECONDS.
    
    The loop will continue until the application is shut down or
    the _health_checker_running flag is set to False.
    """
    global _health_checker_running
    
    logger.info(
        f"Health checker starting (interval: {settings.health_check_interval_seconds}s, "
        f"timeout: {settings.health_check_timeout_seconds}s, "
        f"max failures: {settings.max_consecutive_failures}, "
        f"auto-deregister: {settings.auto_deregister_after_failures})"
    )
    
    cycle_count = 0
    
    while _health_checker_running:
        cycle_count += 1
        
        try:
            logger.debug(f"Health check cycle #{cycle_count} starting")
            
            # Perform checks on all servers
            stats = await check_all_servers()
            
            logger.debug(
                f"Health check cycle #{cycle_count} complete: "
                f"{stats['total_checked']} checked, "
                f"{stats['healthy_count']} healthy, "
                f"{stats['unhealthy_count']} unhealthy"
            )
            
            # Wait for next interval
            await asyncio.sleep(settings.health_check_interval_seconds)
            
        except asyncio.CancelledError:
            logger.info("Health checker received cancellation signal")
            break
            
        except Exception as error:
            logger.error(
                f"Error in health check cycle #{cycle_count}: {error}",
                exc_info=True
            )
            # Continue running even if one cycle fails
            # Wait a bit before retrying
            await asyncio.sleep(10)
    
    logger.info(
        f"Health checker stopped after {cycle_count} cycles"
    )


async def start_health_checker() -> None:
    """Start the background health checker.
    
    This function should be called during application startup to begin
    continuous health monitoring. It creates a background task that runs
    the health check loop.
    
    Raises:
        RuntimeError: If health checker is already running
    """
    global _health_checker_running, _health_checker_task
    
    if _health_checker_running:
        logger.warning("Health checker is already running")
        return
    
    logger.info("Starting health checker background task")
    
    _health_checker_running = True
    _health_checker_task = asyncio.create_task(health_check_loop())
    
    logger.info("Health checker background task started")


async def stop_health_checker() -> None:
    """Stop the background health checker.
    
    This function should be called during application shutdown to gracefully
    stop the health checker. It waits for the current check cycle to complete
    before returning.
    """
    global _health_checker_running, _health_checker_task
    
    if not _health_checker_running:
        logger.debug("Health checker is not running")
        return
    
    logger.info("Stopping health checker...")
    
    # Signal the loop to stop
    _health_checker_running = False
    
    # Cancel the task if it exists
    if _health_checker_task:
        _health_checker_task.cancel()
        
        try:
            # Wait for task to complete cancellation
            await asyncio.wait_for(_health_checker_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Health checker did not stop within timeout")
        except asyncio.CancelledError:
            logger.debug("Health checker task cancelled successfully")
        except Exception as error:
            logger.error(f"Error stopping health checker: {error}", exc_info=True)
        
        _health_checker_task = None
    
    logger.info("Health checker stopped")


def is_health_checker_running() -> bool:
    """Check if the health checker is currently running.
    
    Returns:
        True if the health checker is running, False otherwise
    """
    return _health_checker_running


async def get_health_checker_status() -> dict:
    """Get the current status of the health checker.
    
    Returns:
        Dictionary with health checker status information
    """
    return {
        "running": _health_checker_running,
        "interval_seconds": settings.health_check_interval_seconds,
        "timeout_seconds": settings.health_check_timeout_seconds,
        "max_consecutive_failures": settings.max_consecutive_failures,
        "auto_deregister_enabled": settings.auto_deregister_after_failures
    }


if __name__ == "__main__":
    # Test the health checker
    import os
    
    os.environ["ADMIN_API_KEY"] = "test-key-1234567890"
    os.environ["HEALTH_CHECK_INTERVAL_SECONDS"] = "5"
    
    async def test_health_checker():
        """Test the health checker service."""
        print("Starting health checker test...")
        
        # Start the health checker
        await start_health_checker()
        
        # Let it run for a few cycles
        await asyncio.sleep(20)
        
        # Get status
        status = await get_health_checker_status()
        print(f"Health checker status: {status}")
        
        # Stop the health checker
        await stop_health_checker()
        
        print("Health checker test complete!")
    
    asyncio.run(test_health_checker())

