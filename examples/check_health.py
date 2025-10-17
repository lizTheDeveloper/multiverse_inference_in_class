"""Example script for checking gateway and server health.

This script demonstrates how to monitor the health of the gateway
and registered servers.
"""

import os
import requests
from typing import Optional

# Configuration
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")


def check_gateway_health() -> dict:
    """Check the health of the gateway itself.

    Returns:
        Health status dictionary

    Raises:
        requests.HTTPError: If request fails
    """
    url = f"{GATEWAY_URL}/health"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_server_stats() -> Optional[dict]:
    """Get statistics about registered servers.

    Returns:
        Statistics dictionary or None if not accessible

    Raises:
        requests.HTTPError: If request fails
    """
    if not ADMIN_API_KEY:
        return None

    url = f"{GATEWAY_URL}/admin/stats"
    headers = {"X-API-Key": ADMIN_API_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_server_health_summary() -> Optional[dict]:
    """Get summary of server health status.

    Returns:
        Dictionary with health counts or None if not accessible

    Raises:
        requests.HTTPError: If request fails
    """
    if not ADMIN_API_KEY:
        return None

    url = f"{GATEWAY_URL}/admin/servers"
    headers = {"X-API-Key": ADMIN_API_KEY}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        servers = data.get("servers", [])

        # Count by health status
        healthy = len([s for s in servers if s["health_status"] == "healthy"])
        unhealthy = len([s for s in servers if s["health_status"] == "unhealthy"])
        unknown = len([s for s in servers if s["health_status"] == "unknown"])

        return {
            "total": len(servers),
            "healthy": healthy,
            "unhealthy": unhealthy,
            "unknown": unknown
        }
    else:
        response.raise_for_status()


def print_health_status(status: dict):
    """Print health status in a formatted way.

    Args:
        status: Health status dictionary
    """
    status_symbol = "✓" if status.get("status") == "healthy" else "✗"
    print(f"{status_symbol} Gateway Status: {status.get('status', 'unknown')}")
    print(f"  Service: {status.get('service', 'unknown')}")
    print(f"  Version: {status.get('version', 'unknown')}")
    print(f"  Database: {status.get('database', 'unknown')}")


def print_server_stats(stats: dict):
    """Print server statistics.

    Args:
        stats: Statistics dictionary
    """
    print(f"\nServer Statistics:")
    print(f"  Total Servers: {stats.get('total_servers', 0)}")
    print(f"  Total Models: {stats.get('total_models', 0)}")

    health = stats.get('servers_by_health', {})
    print(f"  Healthy: {health.get('healthy', 0)}")
    print(f"  Unhealthy: {health.get('unhealthy', 0)}")
    print(f"  Unknown: {health.get('unknown', 0)}")


def main():
    """Main function to check health."""
    print("=" * 60)
    print("Multiverse Gateway - Health Check")
    print("=" * 60)
    print()

    try:
        # Check gateway health
        print("Checking gateway health...")
        health = check_gateway_health()
        print_health_status(health)

        # Get server stats if admin key is available
        if ADMIN_API_KEY:
            print("\nChecking server health...")
            stats = get_server_stats()
            if stats:
                print_server_stats(stats)

            # Get detailed health summary
            health_summary = get_server_health_summary()
            if health_summary:
                print(f"\nServer Health Summary:")
                print(f"  Total: {health_summary['total']}")
                print(f"  Healthy: {health_summary['healthy']}")
                print(f"  Unhealthy: {health_summary['unhealthy']}")
                print(f"  Unknown: {health_summary['unknown']}")

                # Calculate health percentage
                if health_summary['total'] > 0:
                    health_pct = (health_summary['healthy'] / health_summary['total']) * 100
                    print(f"  Health Rate: {health_pct:.1f}%")
        else:
            print("\nNote: Set ADMIN_API_KEY to see server health details")

        print()
        print("=" * 60)
        print("Health check complete!")
        print("=" * 60)

    except requests.HTTPError as error:
        print(f"\nHealth check failed: {error}")
        if error.response:
            print(f"Status: {error.response.status_code}")
            print(f"Response: {error.response.text}")
    except Exception as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()
