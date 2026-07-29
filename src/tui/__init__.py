from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_MODE_MANAGER: Any = None
_MUTATION_TRACKER: Any = None


def _get_mode_manager():
    global _MODE_MANAGER
    if _MODE_MANAGER is None:
        from src.modes import ModeManager
        _MODE_MANAGER = ModeManager()
    return _MODE_MANAGER


def _get_mutation_tracker():
    global _MUTATION_TRACKER
    if _MUTATION_TRACKER is None:
        from src.mutation import FileMutationTracker
        _MUTATION_TRACKER = FileMutationTracker(".")
    return _MUTATION_TRACKER


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
    from rich.markdown import Markdown
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.styles import Style

    console = Console()
    history_path = Path.home() / ".edspike_history"
    history_path.parent.mkdir(parents=True, exist_ok=True)

    mode_mgr = _get_mode_manager()
    tracker = _get_mutation_tracker()
    tracker._base = Path(working_dir).resolve() if working_dir else Path(".").resolve()
    tracker.snapshot()

    try:
        psession = PromptSession(
            history=FileHistory(str(history_path)),
        )
    except Exception:
        psession = PromptSession()

    style = Style.from_dict({
        "prompt": "ansicyan bold",
    })

    console.print(Panel(
        "[bold cyan]EDSPiKE[/bold cyan] - AI Coding Assistant",
        subtitle="[/bold]Type /help for commands, Ctrl+C to exit[/bold]",
        border_style="cyan",
    ))

    while True:
        mode = mode_mgr.get_current()
        prompt_str = f"\033[36m[{mode.name}]\033[0m >>> "

        try:
            text = psession.prompt(prompt_str, style=style)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Goodbye![/yellow]")
            break

        text = text.strip()
        if not text:
            continue

        if text.startswith("/"):
            _handle_command(text, console, mode_mgr, tracker, working_dir)
        else:
            _process_prompt(text, console, mode_mgr, working_dir)


def _handle_command(text: str, console: Any, mode_mgr: Any, tracker: Any, working_dir: str) -> None:
    cmd = text.split()[0].lower()
    args = text.split()[1:]

    if cmd in ("/help",):
        _show_help(console)
    elif cmd in ("/clear",):
        console.clear()
    elif cmd in ("/exit", "/quit"):
        raise EOFError()
    elif cmd in ("/plan",):
        mode_mgr.set_mode("plan")
        console.print("[yellow]Switched to Plan mode (read-only)[/yellow]")
    elif cmd in ("/build",):
        mode_mgr.set_mode("build")
        console.print("[green]Switched to Build mode (full access)[/green]")
    elif cmd in ("/mode",):
        if args:
            try:
                mode_mgr.set_mode(args[0])
                console.print(f"[green]Switched to {args[0]} mode[/green]")
            except KeyError:
                modes = ", ".join(m.id for m in mode_mgr.list_modes())
                console.print(f"[red]Unknown mode. Available: {modes}[/red]")
        else:
            current = mode_mgr.get_current()
            console.print(f"[cyan]Current mode: {current.name}[/cyan]")
            for m in mode_mgr.list_modes():
                marker = " *" if m.id == current.id else ""
                console.print(f"  {m.id}{marker} - {m.description}")
    elif cmd in ("/undo",):
        undone = tracker.undo_last()
        if undone:
            console.print(f"[green]Undone: {undone.type.value} {undone.path}[/green]")
        else:
            console.print("[yellow]Nothing to undo[/yellow]")
    elif cmd in ("/redo",):
        console.print("[yellow]Redo not yet supported[/yellow]")
    elif cmd in ("/diff",):
        changes = tracker.detect_changes()
        if not changes:
            console.print("[yellow]No uncommitted changes[/yellow]")
        else:
            from rich.table import Table
            table = Table(title="Recent Changes")
            table.add_column("Type", style="cyan")
            table.add_column("Path")
            table.add_column("Old")
            table.add_column("New")
            for c in changes[-10:]:
                old = c.old_hash[:8] if c.old_hash else ""
                new = c.new_hash[:8] if c.new_hash else ""
                table.add_row(c.type.value, c.path, old, new)
            console.print(table)
    else:
        console.print(f"[red]Unknown command: {text}. Type /help for commands.[/red]")


def _process_prompt(text: str, console: Any, mode_mgr: Any, working_dir: str) -> None:
    try:
        from src.config import load_settings
        from src.providers import get_provider

        settings = load_settings()
        provider = get_provider(settings.providers.default_provider or "openai")

        if not provider:
            console.print("[red]No provider configured.[/red]")
            return

        model = settings.providers.default_model or "gpt-4"
        mode = mode_mgr.get_current()

        system_mode_hint = ""
        if mode.id == "plan":
            system_mode_hint = "You are in PLAN mode. Analyze and suggest changes but DO NOT modify any files."
        elif mode.id == "explore":
            system_mode_hint = "You are in EXPLORE mode. Search and read files only. Do not modify anything."

        enhanced_prompt = text
        if system_mode_hint:
            enhanced_prompt = f"[{mode.name} mode]\n{system_mode_hint}\n\nUser: {text}"

        with console.status("[cyan]Thinking...[/cyan]"):
            response = provider.generate(enhanced_prompt, model=model)

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
    table.add_row("/build", "Switch to Build mode (full access)")
    table.add_row("/plan", "Switch to Plan mode (read-only)")
    table.add_row("/mode [name]", "Show or switch agent mode")
    table.add_row("/undo", "Undo last file change")
    table.add_row("/diff", "Show recent file changes")

    console.print(table)


def _fallback_repl(working_dir: str) -> None:
    print("TUI requires prompt_toolkit. Install with: pip install prompt_toolkit")
    print("Falling back to simple REPL. Type '/exit' to quit.\n")
    mode_mgr = _get_mode_manager()

    while True:
        mode = mode_mgr.get_current()
        try:
            text = input(f"[{mode.name}] >>> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        text = text.strip()
        if not text:
            continue
        if text == "/exit" or text == "/quit":
            break
        elif text == "/help":
            print("Commands: /help, /clear, /build, /plan, /mode, /undo, /diff, /exit, /quit")
        elif text == "/build":
            mode_mgr.set_mode("build")
            print("Switched to Build mode")
        elif text == "/plan":
            mode_mgr.set_mode("plan")
            print("Switched to Plan mode")
        elif text.startswith("/"):
            print(f"Unknown: {text}")
        else:
            print(f"Echo: {text}")
