"""Example script for using the Multiverse Inference Gateway with OpenAI library.

This script demonstrates how to use models hosted on the gateway
using the standard OpenAI Python library.
"""

import os
from openai import OpenAI

# Configuration
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-2-7b")


def list_models(client: OpenAI) -> None:
    """List all available models on the gateway.

    Args:
        client: OpenAI client instance
    """
    print("Available Models:")
    print("-" * 50)

    models = client.models.list()

    for model in models.data:
        print(f"  • {model.id}")

    print(f"\nTotal: {len(models.data)} model(s)")
    print()


def chat_completion_example(client: OpenAI, model: str) -> None:
    """Example of making a chat completion request.

    Args:
        client: OpenAI client instance
        model: Model name to use
    """
    print(f"Chat Completion Example (model: {model}):")
    print("-" * 50)

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]

    print(f"User: {messages[1]['content']}")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )

        assistant_message = response.choices[0].message.content
        print(f"Assistant: {assistant_message}")

        # Show usage stats if available
        if response.usage:
            print(f"\nTokens used: {response.usage.total_tokens}")

    except Exception as error:
        print(f"Error: {error}")

    print()


def text_completion_example(client: OpenAI, model: str) -> None:
    """Example of making a text completion request.

    Args:
        client: OpenAI client instance
        model: Model name to use
    """
    print(f"Text Completion Example (model: {model}):")
    print("-" * 50)

    prompt = "Once upon a time, in a land far away,"

    print(f"Prompt: {prompt}")

    try:
        response = client.completions.create(
            model=model,
            prompt=prompt,
            max_tokens=50,
            temperature=0.8
        )

        completion = response.choices[0].text
        print(f"Completion: {completion}")

        # Show usage stats if available
        if response.usage:
            print(f"\nTokens used: {response.usage.total_tokens}")

    except Exception as error:
        print(f"Error: {error}")

    print()


def streaming_chat_example(client: OpenAI, model: str) -> None:
    """Example of streaming chat completion.

    Args:
        client: OpenAI client instance
        model: Model name to use
    """
    print(f"Streaming Chat Example (model: {model}):")
    print("-" * 50)

    messages = [
        {"role": "user", "content": "Tell me a short story about a robot."}
    ]

    print(f"User: {messages[0]['content']}")
    print("Assistant: ", end="", flush=True)

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            max_tokens=200
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)

        print("\n")

    except Exception as error:
        print(f"\nError: {error}")

    print()


def main():
    """Main function to demonstrate gateway usage."""
    # Initialize OpenAI client pointing to the gateway
    client = OpenAI(
        base_url=GATEWAY_URL,
        api_key="not-needed"  # Gateway doesn't require client API keys by default
    )

    print("=" * 50)
    print("Multiverse Inference Gateway - Usage Examples")
    print("=" * 50)
    print()

    # List available models
    try:
        list_models(client)
    except Exception as error:
        print(f"Failed to list models: {error}")
        print("Make sure the gateway is running and accessible.")
        return

    # Run examples
    try:
        chat_completion_example(client, MODEL_NAME)
        text_completion_example(client, MODEL_NAME)
        streaming_chat_example(client, MODEL_NAME)

    except Exception as error:
        print(f"Error running examples: {error}")

    print("=" * 50)
    print("Examples complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
