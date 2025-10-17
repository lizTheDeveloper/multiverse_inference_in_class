"""Configuration management for the inference gateway.

This module uses pydantic-settings to manage configuration from environment
variables and .env files. All configuration is validated at startup.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file.
    
    All settings can be overridden by environment variables. For example,
    DATABASE_URL can be set as an environment variable to override the default.
    """
    
    # Application settings
    app_name: str = Field(
        default="Multiverse Inference Gateway",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    # Server settings
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind the server to"
    )
    port: int = Field(
        default=8000,
        description="Port to bind the server to"
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload on code changes (development only)"
    )
    
    # Database settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///./gateway.db",
        description="Database connection URL"
    )
    database_wal_mode: bool = Field(
        default=True,
        description="Enable SQLite WAL mode for better concurrent access"
    )
    
    # Security settings
    admin_api_key: str = Field(
        default="",
        description="API key for admin endpoints (required)"
    )
    require_client_api_key: bool = Field(
        default=False,
        description="Whether to require API key for client inference endpoints"
    )
    client_api_keys: list[str] = Field(
        default_factory=list,
        description="List of valid client API keys (if required)"
    )
    
    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_dir: str = Field(
        default="logs",
        description="Directory to store log files"
    )
    log_file: str = Field(
        default="gateway.log",
        description="Name of the main log file"
    )
    log_max_bytes: int = Field(
        default=10_485_760,  # 10 MB
        description="Maximum size of log file before rotation"
    )
    log_backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep"
    )
    enable_console_logging: bool = Field(
        default=True,
        description="Enable logging to console"
    )
    enable_file_logging: bool = Field(
        default=True,
        description="Enable logging to file"
    )
    
    # Health check settings
    health_check_interval_seconds: int = Field(
        default=60,
        description="Interval between health checks (seconds)"
    )
    health_check_timeout_seconds: int = Field(
        default=10,
        description="Timeout for individual health checks (seconds)"
    )
    max_consecutive_failures: int = Field(
        default=3,
        description="Number of consecutive failures before marking server as unhealthy"
    )
    auto_deregister_after_failures: bool = Field(
        default=True,
        description="Automatically deregister servers after max consecutive failures"
    )
    
    # Request routing settings
    request_timeout_seconds: int = Field(
        default=300,
        description="Timeout for forwarding requests to backend servers (seconds)"
    )
    max_retry_attempts: int = Field(
        default=2,
        description="Maximum number of retry attempts with different servers"
    )
    round_robin_enabled: bool = Field(
        default=True,
        description="Enable round-robin load balancing"
    )
    
    # Rate limiting settings
    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable rate limiting"
    )
    rate_limit_requests_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute per IP address"
    )
    
    # Request/response settings
    max_request_body_size: int = Field(
        default=1_048_576,  # 1 MB
        description="Maximum size of request body in bytes"
    )
    include_gateway_server_id_header: bool = Field(
        default=True,
        description="Include X-Gateway-Server-ID header in responses"
    )
    
    # CORS settings
    cors_enabled: bool = Field(
        default=True,
        description="Enable CORS middleware"
    )
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="List of allowed CORS origins"
    )
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["*"],
        description="List of allowed CORS methods"
    )
    cors_allow_headers: list[str] = Field(
        default_factory=lambda: ["*"],
        description="List of allowed CORS headers"
    )
    
    # Validators
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate that log level is one of the allowed values."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        value_upper = value.upper()
        if value_upper not in allowed_levels:
            raise ValueError(
                f"log_level must be one of {allowed_levels}, got {value}"
            )
        return value_upper
    
    @field_validator("admin_api_key")
    @classmethod
    def validate_admin_api_key(cls, value: str) -> str:
        """Validate that admin API key is set in production."""
        if not value:
            raise ValueError(
                "admin_api_key must be set in environment or .env file"
            )
        if len(value) < 16:
            raise ValueError(
                "admin_api_key must be at least 16 characters long"
            )
        return value
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, value: int) -> int:
        """Validate port number is in valid range."""
        if not 1 <= value <= 65535:
            raise ValueError(f"port must be between 1 and 65535, got {value}")
        return value
    
    @field_validator("health_check_interval_seconds")
    @classmethod
    def validate_health_check_interval(cls, value: int) -> int:
        """Validate health check interval is reasonable."""
        if value < 10:
            raise ValueError("health_check_interval_seconds must be at least 10")
        return value
    
    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env file
    )
    
    def get_database_path(self) -> Optional[Path]:
        """Get the path to the SQLite database file if using SQLite.
        
        Returns:
            Path to database file, or None if not using SQLite
        """
        if self.database_url.startswith("sqlite"):
            # Extract path from URL
            db_path = self.database_url.split("///")[-1]
            return Path(db_path)
        return None
    
    def is_sqlite(self) -> bool:
        """Check if database is SQLite.
        
        Returns:
            True if using SQLite, False otherwise
        """
        return self.database_url.startswith("sqlite")


# Global settings instance
# This will be initialized when the module is imported
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance.
    
    This function implements a singleton pattern for settings. The settings
    are loaded once and cached for the lifetime of the application.
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment and .env file.
    
    This is useful for testing or when configuration changes at runtime.
    
    Returns:
        New settings instance
    """
    global _settings
    _settings = Settings()
    return _settings


if __name__ == "__main__":
    # Test configuration loading
    import os
    
    # Set test environment variables
    os.environ["ADMIN_API_KEY"] = "test_key_1234567890"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["PORT"] = "8080"
    
    settings = get_settings()
    
    print(f"App Name: {settings.app_name}")
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
    print(f"Log Level: {settings.log_level}")
    print(f"Database URL: {settings.database_url}")
    print(f"Database Path: {settings.get_database_path()}")
    print(f"Is SQLite: {settings.is_sqlite()}")
    print(f"Admin API Key: {'*' * len(settings.admin_api_key)}")

