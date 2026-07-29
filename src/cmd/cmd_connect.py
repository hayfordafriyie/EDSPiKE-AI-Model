from __future__ import annotations

import sys
from typing import Any


def cmd_connect(args: list[str]) -> int:
    print("=== Provider Setup ===")
    print("Available providers: openai, anthropic, google, deepseek, local")
    print()

    try:
        provider = input("Provider [openai]: ").strip() or "openai"
    except (EOFError, KeyboardInterrupt):
        print()
        return 1

    if provider == "local":
        print(f"\nUsing local model. No API key needed.")
        print("Run: export EDSPIKE_DEFAULT_PROVIDER=local")
        return 0

    try:
        api_key = input(f"API key for {provider}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return 1

    if not api_key:
        print("Error: API key is required", file=sys.stderr)
        return 1

    env_var = f"EDSPIKE_{provider.upper()}_API_KEY"
    print(f"\nSet environment variable:")
    print(f"  export {env_var}='{api_key[:8]}...'")
    print(f"  export EDSPIKE_DEFAULT_PROVIDER={provider}")
    print()
    print("To persist, add these to your .env file or shell profile.")
    return 0
