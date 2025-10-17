"""URL validation utilities to prevent SSRF and other security issues.

This module provides functions to validate URLs before making requests to them,
preventing Server-Side Request Forgery (SSRF) attacks and other security issues.
"""

import ipaddress
import re
from typing import Tuple
from urllib.parse import urlparse

from app.utils.logger import get_logger

logger = get_logger(__name__)


# Private IP ranges to block (SSRF prevention)
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),       # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),    # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),   # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
]


# Blocked hostnames (case-insensitive)
BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "[::1]",
    "::1",
}


def is_private_ip(ip_address: str) -> bool:
    """Check if an IP address is in a private range.
    
    Args:
        ip_address: IP address string to check
    
    Returns:
        True if the IP is in a private range, False otherwise
    """
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        for network in PRIVATE_IP_RANGES:
            if ip_obj in network:
                return True
        return False
    except ValueError:
        # Invalid IP address
        return False


def validate_url(url: str) -> Tuple[bool, str]:
    """Validate a URL for security issues.
    
    This function checks for:
    - Valid URL scheme (http/https only)
    - Blocked hostnames (localhost, etc.)
    - Private IP addresses (SSRF prevention)
    - Malformed URLs
    
    Args:
        url: URL string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if URL is safe to use, False otherwise
        - error_message: Description of the validation error, or empty string if valid
    
    Examples:
        >>> validate_url("https://example.com/api")
        (True, "")
        
        >>> validate_url("http://localhost:8000")
        (False, "URL hostname is blocked: localhost")
        
        >>> validate_url("https://192.168.1.1")
        (False, "URL resolves to a private IP address")
    """
    # Basic URL format check
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as error:
        logger.warning(f"Failed to parse URL: {url}, error: {error}")
        return False, f"Invalid URL format: {str(error)}"
    
    # Check scheme (only http and https allowed)
    if parsed.scheme not in ("http", "https"):
        return False, f"URL scheme must be http or https, got: {parsed.scheme}"
    
    # Extract hostname
    hostname = parsed.hostname
    if not hostname:
        return False, "URL must contain a valid hostname"
    
    # Check for blocked hostnames (case-insensitive)
    if hostname.lower() in BLOCKED_HOSTNAMES:
        return False, f"URL hostname is blocked: {hostname}"
    
    # Check if hostname is an IP address
    try:
        ip_obj = ipaddress.ip_address(hostname)
        
        # Check if it's a private IP
        if is_private_ip(hostname):
            return False, f"URL resolves to a private IP address: {hostname}"
        
        logger.info(f"URL uses IP address directly: {hostname}")
        
    except ValueError:
        # Hostname is not an IP address, it's a domain name
        # Check for suspicious patterns in domain name
        
        # Block internal/local TLDs
        blocked_tlds = [".local", ".internal", ".lan", ".corp"]
        for tld in blocked_tlds:
            if hostname.lower().endswith(tld):
                return False, f"URL uses blocked TLD: {tld}"
        
        # Check for localhost variations
        if "localhost" in hostname.lower():
            return False, f"URL contains 'localhost' in hostname: {hostname}"
    
    # Additional security checks
    
    # Check for @ symbol in URL (could be used for confusion)
    if "@" in parsed.netloc:
        return False, "URL contains @ symbol, which is not allowed"
    
    # Check for suspicious ports (some commonly blocked)
    if parsed.port:
        # Allow most ports, but block some system ports
        blocked_ports = {22, 23, 25, 110, 143, 3306, 5432, 6379, 27017}
        if parsed.port in blocked_ports:
            logger.warning(f"URL uses potentially dangerous port: {parsed.port}")
            return False, f"URL uses blocked port: {parsed.port}"
    
    # URL passes all validation checks
    return True, ""


def validate_and_normalize_url(url: str) -> Tuple[bool, str, str]:
    """Validate and normalize a URL.
    
    This function validates the URL and also normalizes it by:
    - Converting to lowercase scheme and hostname
    - Removing default ports (80 for http, 443 for https)
    - Removing trailing slashes
    - Removing fragment identifiers
    
    Args:
        url: URL string to validate and normalize
    
    Returns:
        Tuple of (is_valid, normalized_url, error_message)
        - is_valid: True if URL is safe to use, False otherwise
        - normalized_url: Normalized URL string (empty if invalid)
        - error_message: Description of the validation error, or empty string if valid
    """
    # First validate
    is_valid, error_message = validate_url(url)
    
    if not is_valid:
        return False, "", error_message
    
    # Normalize the URL
    try:
        parsed = urlparse(url)
        
        # Normalize scheme and hostname to lowercase
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname.lower() if parsed.hostname else ""
        
        # Handle port (remove default ports)
        port = parsed.port
        if port:
            if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
                port_str = ""
            else:
                port_str = f":{port}"
        else:
            port_str = ""
        
        # Reconstruct netloc
        netloc = f"{hostname}{port_str}"
        
        # Build normalized URL (without fragment)
        path = parsed.path.rstrip("/") if parsed.path else ""
        query = f"?{parsed.query}" if parsed.query else ""
        
        normalized_url = f"{scheme}://{netloc}{path}{query}"
        
        return True, normalized_url, ""
        
    except Exception as error:
        logger.error(f"Failed to normalize URL: {url}, error: {error}")
        return False, "", f"Failed to normalize URL: {str(error)}"


def is_url_similar(url1: str, url2: str) -> bool:
    """Check if two URLs are essentially the same (ignoring minor differences).
    
    This is useful for detecting duplicate registrations.
    
    Args:
        url1: First URL
        url2: Second URL
    
    Returns:
        True if URLs are similar, False otherwise
    """
    _, normalized1, _ = validate_and_normalize_url(url1)
    _, normalized2, _ = validate_and_normalize_url(url2)
    
    if not normalized1 or not normalized2:
        # If normalization failed, do simple comparison
        return url1.lower().rstrip("/") == url2.lower().rstrip("/")
    
    return normalized1 == normalized2


if __name__ == "__main__":
    # Test the validation functions
    test_urls = [
        ("https://example.com/api", True, "Valid public URL"),
        ("http://localhost:8000", False, "Localhost blocked"),
        ("https://127.0.0.1", False, "Loopback IP blocked"),
        ("https://192.168.1.1", False, "Private IP blocked"),
        ("https://10.0.0.1", False, "Private IP blocked"),
        ("ftp://example.com", False, "Invalid scheme"),
        ("https://abc123.ngrok.io", True, "Valid ngrok URL"),
        ("https://example.com:3306", False, "Blocked port"),
        ("https://user@example.com", False, "@ symbol not allowed"),
        ("https://test.local", False, "Blocked TLD"),
    ]
    
    print("URL Validation Tests:")
    print("=" * 80)
    
    for url, expected_valid, description in test_urls:
        is_valid, error = validate_url(url)
        status = "✓" if is_valid == expected_valid else "✗"
        print(f"{status} {description}")
        print(f"  URL: {url}")
        print(f"  Valid: {is_valid}, Expected: {expected_valid}")
        if error:
            print(f"  Error: {error}")
        print()

