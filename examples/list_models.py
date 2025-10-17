"""Example script for listing available models on the gateway.

This script demonstrates how to query the gateway for available models.
"""

import os
import requests
from typing import List, Dict

# Configuration
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")


def list_models() -> List[Dict]:
    """List all available models on the gateway.

    Returns:
        List of model dictionaries

    Raises:
        requests.HTTPError: If request fails
    """
    url = f"{GATEWAY_URL}/v1/models"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data.get("data", [])
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        response.raise_for_status()


def main():
    """Main function to list models."""
    print("=" * 50)
    print("Available Models on Gateway")
    print("=" * 50)
    print()

    try:
        models = list_models()

        if not models:
            print("No models currently available.")
            print("Register a server first using examples/register_server.py")
        else:
            print(f"Found {len(models)} available model(s):")
            print()

            for model in models:
                print(f"  • {model['id']}")
                if model.get('owned_by'):
                    print(f"    Owned by: {model['owned_by']}")
                if model.get('created'):
                    from datetime import datetime
                    created_date = datetime.fromtimestamp(model['created'])
                    print(f"    Created: {created_date}")
                print()

        print("=" * 50)

    except requests.HTTPError as error:
        print(f"\nRequest failed: {error}")
    except Exception as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()
