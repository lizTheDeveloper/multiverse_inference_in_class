"""Database management and schema definitions for the inference gateway.

This module handles:
- Database connection management
- Schema creation and migrations
- SQLite WAL mode configuration
- Connection pooling for async operations
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
import aiosqlite

from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Database schema version for future migrations
SCHEMA_VERSION = 1


# SQL schema for model_servers table
MODEL_SERVERS_SCHEMA = """
CREATE TABLE IF NOT EXISTS model_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_id TEXT UNIQUE NOT NULL,
    model_name TEXT NOT NULL,
    endpoint_url TEXT NOT NULL,
    api_key TEXT,
    owner_name TEXT,
    owner_email TEXT,
    
    -- Health status fields
    health_status TEXT NOT NULL DEFAULT 'unknown',
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    last_checked_at TIMESTAMP,
    last_successful_request_at TIMESTAMP,
    
    -- Status fields
    is_active INTEGER NOT NULL DEFAULT 1,
    
    -- Audit fields
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    description TEXT,
    tags TEXT,
    
    -- Constraints
    CHECK (health_status IN ('healthy', 'unhealthy', 'unknown')),
    CHECK (is_active IN (0, 1)),
    CHECK (consecutive_failures >= 0)
);
"""


# Indexes for common queries
MODEL_SERVERS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_model_name ON model_servers(model_name);",
    "CREATE INDEX IF NOT EXISTS idx_health_status ON model_servers(health_status);",
    "CREATE INDEX IF NOT EXISTS idx_is_active ON model_servers(is_active);",
    "CREATE INDEX IF NOT EXISTS idx_model_health ON model_servers(model_name, health_status, is_active);",
    "CREATE INDEX IF NOT EXISTS idx_registration_id ON model_servers(registration_id);",
]


# Optional: Health checks history table for tracking
HEALTH_CHECKS_SCHEMA = """
CREATE TABLE IF NOT EXISTS health_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    check_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    
    FOREIGN KEY (server_id) REFERENCES model_servers(id) ON DELETE CASCADE,
    CHECK (status IN ('success', 'failure'))
);
"""


HEALTH_CHECKS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_health_server_id ON health_checks(server_id);",
    "CREATE INDEX IF NOT EXISTS idx_health_check_time ON health_checks(check_time);",
]


# Schema version table for migrations
SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_database() -> None:
    """Initialize the database with the required schema.
    
    This function:
    - Creates the database file if it doesn't exist
    - Enables WAL mode for better concurrent access
    - Creates all required tables and indexes
    - Records schema version
    
    Raises:
        Exception: If database initialization fails
    """
    settings = get_settings()
    
    # Get database path
    if not settings.is_sqlite():
        logger.warning("Non-SQLite database detected, skipping schema initialization")
        return
    
    db_path = settings.get_database_path()
    if db_path is None:
        raise ValueError("Could not determine database path from settings")
    
    logger.info(f"Initializing database at {db_path}")
    
    # Create directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Open connection to create database file and enable WAL mode
        async with aiosqlite.connect(str(db_path)) as connection:
            # Enable WAL mode for better concurrent access
            if settings.database_wal_mode:
                await connection.execute("PRAGMA journal_mode=WAL;")
                logger.info("Enabled WAL mode for SQLite database")
            
            # Enable foreign keys
            await connection.execute("PRAGMA foreign_keys=ON;")
            
            # Create schema version table
            await connection.execute(SCHEMA_VERSION_TABLE)
            
            # Check current schema version
            cursor = await connection.execute(
                "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            current_version = row[0] if row else 0
            
            if current_version < SCHEMA_VERSION:
                logger.info(
                    f"Upgrading database schema from version {current_version} "
                    f"to {SCHEMA_VERSION}"
                )
                
                # Create model_servers table
                await connection.execute(MODEL_SERVERS_SCHEMA)
                logger.info("Created model_servers table")
                
                # Create indexes
                for index_sql in MODEL_SERVERS_INDEXES:
                    await connection.execute(index_sql)
                logger.info(f"Created {len(MODEL_SERVERS_INDEXES)} indexes on model_servers")
                
                # Optionally create health_checks table (for Phase 6)
                # Uncomment when implementing historical health tracking
                # await connection.execute(HEALTH_CHECKS_SCHEMA)
                # for index_sql in HEALTH_CHECKS_INDEXES:
                #     await connection.execute(index_sql)
                # logger.info("Created health_checks table")
                
                # Update schema version
                await connection.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (SCHEMA_VERSION,)
                )
                
                await connection.commit()
                logger.info(f"Database schema upgraded to version {SCHEMA_VERSION}")
            else:
                logger.info(f"Database schema is up to date (version {current_version})")
        
        logger.info("Database initialization completed successfully")
        
    except Exception as error:
        logger.error(f"Failed to initialize database: {error}", exc_info=True)
        raise


async def get_db_connection() -> aiosqlite.Connection:
    """Get an async database connection.
    
    Returns:
        Async database connection
    
    Raises:
        Exception: If connection fails
    """
    settings = get_settings()
    
    if not settings.is_sqlite():
        raise ValueError("Only SQLite databases are currently supported")
    
    db_path = settings.get_database_path()
    if db_path is None:
        raise ValueError("Could not determine database path from settings")
    
    connection = await aiosqlite.connect(str(db_path))
    connection.row_factory = aiosqlite.Row  # Enable column access by name
    
    # Enable foreign keys
    await connection.execute("PRAGMA foreign_keys=ON;")
    
    return connection


async def close_database() -> None:
    """Close any open database connections and perform cleanup.
    
    This is called during application shutdown.
    """
    logger.info("Closing database connections")
    # With aiosqlite, connections are typically managed per-request
    # No global connection pool to close
    logger.info("Database connections closed")


def get_timestamp() -> str:
    """Get current timestamp in ISO format for database storage.
    
    Returns:
        ISO format timestamp string
    """
    return datetime.utcnow().isoformat()


async def health_check_database() -> bool:
    """Check if database is accessible and healthy.
    
    Returns:
        True if database is healthy, False otherwise
    """
    try:
        connection = await get_db_connection()
        try:
            await connection.execute("SELECT 1")
            return True
        finally:
            await connection.close()
    except Exception as error:
        logger.error(f"Database health check failed: {error}")
        return False


if __name__ == "__main__":
    # Test database initialization
    import asyncio
    import os
    
    # Set test environment variables
    os.environ["ADMIN_API_KEY"] = "test_key_1234567890"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_gateway.db"
    
    async def test_db():
        """Test database initialization."""
        print("Testing database initialization...")
        await init_database()
        
        print("\nTesting database connection...")
        connection = await get_db_connection()
        cursor = await connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = await cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")
        await connection.close()
        
        print("\nTesting database health check...")
        is_healthy = await health_check_database()
        print(f"Database healthy: {is_healthy}")
        
        print("\nTest completed successfully!")
    
    asyncio.run(test_db())

