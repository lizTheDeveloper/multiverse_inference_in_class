"""Centralized logging module for the inference gateway.

This module provides structured logging with:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Output to both console and file
- Log rotation
- Structured format with timestamps, component names, and request IDs
- Redaction of sensitive information (API keys)
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# ANSI color codes for console output
class LogColors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    DEBUG = "\033[36m"      # Cyan
    INFO = "\033[32m"       # Green
    WARNING = "\033[33m"    # Yellow
    ERROR = "\033[31m"      # Red
    CRITICAL = "\033[35m"   # Magenta


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output."""
    
    COLORS = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color codes for console output."""
        color = self.COLORS.get(record.levelno, LogColors.RESET)
        record.levelname = f"{color}{record.levelname}{LogColors.RESET}"
        return super().format(record)


class SensitiveDataFilter(logging.Filter):
    """Filter that redacts sensitive information from log messages."""
    
    SENSITIVE_PATTERNS = [
        "api_key", "apikey", "api-key", "x-api-key",
        "password", "secret", "token", "authorization"
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from log message."""
        message = record.getMessage().lower()
        
        # Check if any sensitive pattern is in the message
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                # Replace the actual value with [REDACTED]
                # This is a simple implementation; could be more sophisticated
                record.msg = str(record.msg).replace(
                    record.args[0] if record.args else "",
                    "[REDACTED]"
                )
                record.args = ()
        
        return True


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_file: str = "gateway.log",
    max_bytes: int = 10_485_760,  # 10 MB
    backup_count: int = 5,
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """Set up and configure a logger instance.
    
    Args:
        name: Logger name (typically module name or component name)
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        log_file: Name of the log file
        max_bytes: Maximum size of log file before rotation (default: 10 MB)
        backup_count: Number of backup log files to keep (default: 5)
        enable_console: Whether to output logs to console (default: True)
        enable_file: Whether to output logs to file (default: True)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create log format with structured fields
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(funcName)s:%(lineno)d | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Add sensitive data filter
    sensitive_filter = SensitiveDataFilter()
    logger.addFilter(sensitive_filter)
    
    # Console handler with colors
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_formatter = ColoredFormatter(log_format, datefmt=date_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_path / log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(log_format, datefmt=date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific component.
    
    This is a convenience function that returns an existing logger or creates
    a new one with default settings.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_with_request_id(
    logger: logging.Logger,
    level: str,
    message: str,
    request_id: Optional[str] = None,
    **kwargs
) -> None:
    """Log a message with an optional request ID for correlation.
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        request_id: Optional request ID for correlation
        **kwargs: Additional context to include in log message
    """
    if request_id:
        message = f"[Request: {request_id}] {message}"
    
    if kwargs:
        context = " | ".join(f"{key}={value}" for key, value in kwargs.items())
        message = f"{message} | {context}"
    
    log_method = getattr(logger, level.lower())
    log_method(message)


# Create a default logger for the application
default_logger = setup_logger("multiverse_gateway")


if __name__ == "__main__":
    # Test the logging module
    test_logger = setup_logger("test", log_level="DEBUG")
    
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.critical("This is a critical message")
    
    # Test request ID logging
    log_with_request_id(
        test_logger,
        "info",
        "Processing request",
        request_id="req_123",
        user_id="user_456",
        endpoint="/v1/chat/completions"
    )
    
    # Test sensitive data redaction
    test_logger.info("API key: sk-1234567890abcdef")
    test_logger.info("Authorization: Bearer token123")

