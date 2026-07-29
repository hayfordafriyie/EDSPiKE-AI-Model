from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from src.tui import run_tui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edspike",
        description="EDSPiKE AI Model - Terminal AI coding assistant",
    )
    parser.add_argument(
        "prompt", nargs="*",
        help="Prompt to execute in non-interactive mode"
    )
    parser.add_argument(
        "-m", "--model",
        default="",
        help="Model to use (e.g. gpt-4, claude-3)"
    )
    parser.add_argument(
        "-p", "--provider",
        default="",
        help="Provider to use (e.g. openai, anthropic)"
    )
    parser.add_argument(
        "-d", "--dir", "--directory",
        default=".",
        help="Working directory"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress spinner/output in non-interactive mode"
    )
    return parser


def run_cli(args: list[str] | None = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)

    if parsed.version:
        from src import __version__ as ver
        print(f"EDSPiKE v{ver}")
        return 0

    prompt = " ".join(parsed.prompt) if parsed.prompt else ""

    if prompt:
        return _run_noninteractive(prompt, parsed)

    return _run_interactive(parsed)


def _run_noninteractive(prompt: str, parsed: argparse.Namespace) -> int:
    try:
        from src.config import load_settings
        from src.providers import get_provider

        settings = load_settings()

        model = parsed.model or settings.providers.default_model or "gpt-4"
        provider_name = parsed.provider or settings.providers.default_provider or "openai"

        provider = get_provider(provider_name)
        if not provider:
            print(f"Error: Provider '{provider_name}' not found", file=sys.stderr)
            return 1

        if not parsed.quiet:
            print(f"Using {provider_name}/{model}...", file=sys.stderr)

        response = provider.generate(prompt, model=model)
        print(response)
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def _run_interactive(parsed: argparse.Namespace) -> int:
    try:
        run_tui(working_dir=parsed.dir)
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"TUI Error: {e}", file=sys.stderr)
        return 1
