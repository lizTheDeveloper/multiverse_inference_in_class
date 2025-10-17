"""Example script for listing and monitoring registered servers.

This script demonstrates how to view all registered servers and their health status.
"""

import os
import requests
from datetime import datetime
from typing import Optional


# Configuration
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")


def list_servers(
    model_name: Optional[str] = None,
    health_status: Optional[str] = None,
    is_active: Optional[bool] = None
) -> list:
    """List all registered servers with optional filters.

    Args:
        model_name: Filter by model name (optional)
        health_status: Filter by health status: healthy, unhealthy, unknown (optional)
        is_active: Filter by active status (optional)

    Returns:
        List of server dictionaries

    Raises:
        requests.HTTPError: If request fails
    """
    url = f"{GATEWAY_URL}/admin/servers"

    headers = {
        "X-API-Key": ADMIN_API_KEY
    }

    params = {}
    if model_name:
        params["model_name"] = model_name
    if health_status:
        params["health_status"] = health_status
    if is_active is not None:
        params["is_active"] = is_active

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        return data["servers"]
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        response.raise_for_status()


def get_statistics() -> dict:
    """Get gateway statistics.

    Returns:
        Statistics dictionary

    Raises:
        requests.HTTPError: If request fails
    """
    url = f"{GATEWAY_URL}/admin/stats"

    headers = {
        "X-API-Key": ADMIN_API_KEY
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def print_server_info(server: dict) -> None:
    """Print formatted server information.

    Args:
        server: Server dictionary
    """
    status_icon = {
        "healthy": "✓",
        "unhealthy": "✗",
        "unknown": "?"
    }.get(server["health_status"], "?")

    print(f"\n{status_icon} {server['model_name']}")
    print(f"  ID: {server['registration_id']}")
    print(f"  URL: {server['endpoint_url']}")
    print(f"  Status: {server['health_status']}")
    print(f"  Failures: {server['consecutive_failures']}")

    if server.get("owner_name"):
        print(f"  Owner: {server['owner_name']}")

    if server.get("last_checked_at"):
        print(f"  Last Checked: {server['last_checked_at']}")

    if server.get("description"):
        print(f"  Description: {server['description']}")


def main():
    """Main function to list servers and show statistics."""
    if not ADMIN_API_KEY:
        print("Error: ADMIN_API_KEY environment variable not set")
        print("Set it with: export ADMIN_API_KEY='your-api-key'")
        return

    print("=" * 60)
    print("Multiverse Inference Gateway - Server Status")
    print("=" * 60)

    try:
        # Get statistics
        stats = get_statistics()
        print(f"\nStatistics:")
        print(f"  Total Servers: {stats['total_servers']}")
        print(f"  Total Models: {stats['total_models']}")
        print(f"  Healthy: {stats['servers_by_health']['healthy']}")
        print(f"  Unhealthy: {stats['servers_by_health']['unhealthy']}")
        print(f"  Unknown: {stats['servers_by_health']['unknown']}")

        # List all servers
        print("\n" + "-" * 60)
        print("Registered Servers:")
        print("-" * 60)

        servers = list_servers()

        if not servers:
            print("\nNo servers registered yet.")
        else:
            for server in servers:
                print_server_info(server)

        print("\n" + "=" * 60)

        # Show healthy servers only
        print("\nHealthy Servers:")
        healthy = list_servers(health_status="healthy")
        print(f"  {len(healthy)} healthy server(s)")

        # Group by model
        models = {}
        for server in servers:
            model = server["model_name"]
            if model not in models:
                models[model] = []
            models[model].append(server)

        if models:
            print("\nServers by Model:")
            for model, model_servers in models.items():
                healthy_count = len([s for s in model_servers if s["health_status"] == "healthy"])
                print(f"  {model}: {healthy_count}/{len(model_servers)} healthy")

    except requests.HTTPError as error:
        print(f"\nRequest failed: {error}")
    except Exception as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()
