"""Example script for registering a model server with the gateway.

This script demonstrates how to register your model server with the
Multiverse Inference Gateway so others can access your model.
"""

import os
import requests
from typing import Optional

# Configuration
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

# Your server details
MODEL_NAME = "llama-2-7b"  # Change this to your model name
ENDPOINT_URL = "https://your-server.ngrok.io"  # Change this to your server URL
OWNER_NAME = "Your Name"  # Your name
OWNER_EMAIL = "your.email@example.com"  # Your email
DESCRIPTION = "My Llama 2 7B model server"  # Optional description


def register_server(
    model_name: str,
    endpoint_url: str,
    owner_name: Optional[str] = None,
    owner_email: Optional[str] = None,
    description: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict:
    """Register a model server with the gateway.

    Args:
        model_name: Name of the model being served
        endpoint_url: Full URL of your model server
        owner_name: Your name (optional)
        owner_email: Your email (optional)
        description: Description of your server (optional)
        api_key: Backend server API key (optional)

    Returns:
        Registration response with registration_id

    Raises:
        requests.HTTPError: If registration fails
    """
    url = f"{GATEWAY_URL}/admin/register"

    headers = {
        "X-API-Key": ADMIN_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "model_name": model_name,
        "endpoint_url": endpoint_url
    }

    # Add optional fields if provided
    if owner_name:
        data["owner_name"] = owner_name
    if owner_email:
        data["owner_email"] = owner_email
    if description:
        data["description"] = description
    if api_key:
        data["api_key"] = api_key

    print(f"Registering server: {model_name} at {endpoint_url}")

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        result = response.json()
        print(f"✓ Successfully registered!")
        print(f"  Registration ID: {result['registration_id']}")
        print(f"  Model: {result['model_name']}")
        print(f"  Health Status: {result['health_status']}")
        print(f"\nKeep your registration ID safe - you'll need it to update or deregister.")
        return result
    else:
        print(f"✗ Registration failed!")
        print(f"  Status Code: {response.status_code}")
        print(f"  Error: {response.text}")
        response.raise_for_status()


def main():
    """Main function to register a server."""
    if not ADMIN_API_KEY:
        print("Error: ADMIN_API_KEY environment variable not set")
        print("Set it with: export ADMIN_API_KEY='your-api-key'")
        return

    try:
        register_server(
            model_name=MODEL_NAME,
            endpoint_url=ENDPOINT_URL,
            owner_name=OWNER_NAME,
            owner_email=OWNER_EMAIL,
            description=DESCRIPTION
        )
    except requests.HTTPError as error:
        print(f"\nRegistration failed: {error}")
    except Exception as error:
        print(f"\nUnexpected error: {error}")


if __name__ == "__main__":
    main()
