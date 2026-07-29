from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


def run_tui(working_dir: str = ".") -> None:
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.styles import Style
    except ImportError:
        _fallback_repl(working_dir)
        return

    _rich_tui(working_dir)


def _rich_tui(working_dir: str) -> None:
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    from rich.markdown import Markdown
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style

    console = Console()
    history_path = Path.home() / ".edspike_history"
    history_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        session = PromptSession(
            history=FileHistory(str(history_path)),
        )
    except Exception:
        session = PromptSession()

    style = Style.from_dict({
        "prompt": "ansicyan bold",
    })

    console.print(Panel(
        "[bold cyan]EDSPiKE[/bold cyan] - AI Coding Assistant",
        subtitle="Type /help for commands, Ctrl+C to exit",
        border_style="cyan",
    ))

    while True:
        try:
            text = session.prompt(">>> ", style=style)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Goodbye![/yellow]")
            break

        text = text.strip()
        if not text:
            continue

        if text == "/help":
            _show_help(console)
        elif text == "/clear":
            console.clear()
        elif text == "/exit" or text == "/quit":
            break
        elif text.startswith("/"):
            console.print(f"[red]Unknown command: {text}[/red]")
        else:
            _process_prompt(text, console, working_dir)


def _process_prompt(text: str, console: Any, working_dir: str) -> None:
    try:
        from src.config import load_settings
        from src.providers import get_provider

        settings = load_settings()
        provider = get_provider(settings.providers.default_provider or "openai")

        if not provider:
            console.print("[red]No provider configured.[/red]")
            return

        model = settings.providers.default_model or "gpt-4"

        with console.status("[cyan]Thinking...[/cyan]"):
            response = provider.generate(text, model=model)

        console.print(Markdown(response))

    except ImportError:
        console.print(f"[yellow]{text}[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def _show_help(console: Any) -> None:
    from rich.table import Table

    table = Table(title="Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description")

    table.add_row("/help", "Show this help")
    table.add_row("/clear", "Clear screen")
    table.add_row("/exit", "Exit the TUI")
    table.add_row("/quit", "Exit the TUI")

    console.print(table)


def _fallback_repl(working_dir: str) -> None:
    print("TUI requires prompt_toolkit. Install with: pip install prompt_toolkit")
    print("Falling back to simple REPL. Type '/exit' to quit.\n")

    while True:
        try:
            text = input(">>> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        text = text.strip()
        if not text:
            continue
        if text == "/exit" or text == "/quit":
            break
        elif text == "/help":
            print("Commands: /help, /clear, /exit, /quit")
        else:
            print(f"Echo: {text}")
