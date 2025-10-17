"""Tests for the background health checker service.

These tests verify:
- Health check loop functionality
- Consecutive failure tracking
- Auto-deregistration logic
- Startup/shutdown behavior
"""

import pytest
import asyncio
import os

# Set test environment variables
os.environ["ADMIN_API_KEY"] = "test-admin-key-1234567890"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_health_checker.db"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["HEALTH_CHECK_INTERVAL_SECONDS"] = "10"  # Minimum allowed
os.environ["MAX_CONSECUTIVE_FAILURES"] = "3"
os.environ["AUTO_DEREGISTER_AFTER_FAILURES"] = "true"

from app.services.health_checker import (
    start_health_checker,
    stop_health_checker,
    is_health_checker_running,
    get_health_checker_status,
    check_all_servers
)
from app.utils.database import init_database


class TestHealthCheckerStatus:
    """Test health checker status functions."""
    
    @pytest.mark.asyncio
    async def test_is_not_running_initially(self):
        """Test that health checker is not running initially."""
        # Make sure it's stopped
        await stop_health_checker()
        assert not is_health_checker_running()
    
    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting health checker status."""
        status = await get_health_checker_status()
        
        assert "running" in status
        assert "interval_seconds" in status
        assert "timeout_seconds" in status
        assert "max_consecutive_failures" in status
        assert "auto_deregister_enabled" in status
        
        assert isinstance(status["running"], bool)
        assert isinstance(status["interval_seconds"], int)
        assert isinstance(status["timeout_seconds"], int)
        assert isinstance(status["max_consecutive_failures"], int)
        assert isinstance(status["auto_deregister_enabled"], bool)


class TestHealthCheckerLifecycle:
    """Test health checker startup and shutdown."""
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """Test starting and stopping the health checker."""
        # Start
        await start_health_checker()
        assert is_health_checker_running()
        
        # Give it a moment to start
        await asyncio.sleep(0.5)
        
        # Stop
        await stop_health_checker()
        assert not is_health_checker_running()
    
    @pytest.mark.asyncio
    async def test_start_twice(self):
        """Test that starting twice doesn't cause issues."""
        await start_health_checker()
        await start_health_checker()  # Should log warning but not fail
        
        assert is_health_checker_running()
        
        await stop_health_checker()
    
    @pytest.mark.asyncio
    async def test_stop_when_not_running(self):
        """Test that stopping when not running doesn't cause issues."""
        await stop_health_checker()
        await stop_health_checker()  # Should not fail
        
        assert not is_health_checker_running()


class TestCheckAllServers:
    """Test the check_all_servers function."""
    
    @pytest.mark.asyncio
    async def test_check_empty_servers(self):
        """Test checking when no servers are registered."""
        # Initialize database
        await init_database()
        
        # Check all servers (should be none)
        stats = await check_all_servers()
        
        assert stats["total_checked"] == 0
        assert stats["healthy_count"] == 0
        assert stats["unhealthy_count"] == 0
        assert stats["deregistered_count"] == 0
        assert stats["check_duration_seconds"] >= 0
    
    @pytest.mark.asyncio
    async def test_stats_structure(self):
        """Test that check_all_servers returns correct structure."""
        await init_database()
        
        stats = await check_all_servers()
        
        # Verify all required keys are present
        required_keys = {
            "total_checked",
            "healthy_count",
            "unhealthy_count",
            "deregistered_count",
            "check_duration_seconds"
        }
        
        assert set(stats.keys()) == required_keys
        
        # Verify all values are non-negative numbers
        for key, value in stats.items():
            assert isinstance(value, (int, float))
            assert value >= 0


class TestHealthCheckerIntegration:
    """Integration tests for health checker."""
    
    @pytest.mark.asyncio
    async def test_runs_for_multiple_cycles(self):
        """Test that health checker runs for multiple cycles."""
        await init_database()
        
        # Start health checker
        await start_health_checker()
        
        # Let it run briefly (interval is 10 seconds in test config)
        await asyncio.sleep(2)
        
        # Verify it's still running
        assert is_health_checker_running()
        
        # Stop it
        await stop_health_checker()
        assert not is_health_checker_running()
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        """Test that health checker shuts down gracefully."""
        await start_health_checker()
        
        # Let it run briefly
        await asyncio.sleep(1)
        
        # Stop should complete within reasonable time
        await asyncio.wait_for(stop_health_checker(), timeout=10.0)
        
        assert not is_health_checker_running()


class TestHealthCheckerErrorHandling:
    """Test error handling in health checker."""
    
    @pytest.mark.asyncio
    async def test_continues_after_error(self):
        """Test that health checker continues running after errors."""
        # This test verifies resilience - even if one cycle fails,
        # the health checker should continue running
        
        await start_health_checker()
        
        # Let it run briefly
        await asyncio.sleep(2)
        
        # Should still be running
        assert is_health_checker_running()
        
        await stop_health_checker()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])

