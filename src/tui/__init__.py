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
    from prompt_toolkit.keys import Keys
    from prompt_toolkit.key_binding import KeyBindings

    console = Console()
    history_path = Path.home() / ".edspike_history"
    history_path.parent.mkdir(parents=True, exist_ok=True)

    mode_mgr = _get_mode_manager()
    tracker = _get_mutation_tracker()
    tracker._base = Path(working_dir).resolve() if working_dir else Path(".").resolve()
    tracker.snapshot()

    kb = KeyBindings()

    @kb.add("tab")
    def _tab_switch(event):
        current = mode_mgr.get_current()
        next_mode = "plan" if current.id == "build" else "build"
        mode_mgr.set_mode(next_mode)
        mode = mode_mgr.get_current()
        color = {"build": "green", "plan": "yellow"}.get(mode.id, "cyan")
        console.print(f"[{color}]Switched to {mode.name} mode[/{color}]")

    @kb.add("c-c")
    def _exit(event):
        raise EOFError()

    try:
        from prompt_toolkit.completion import Completer, Completion

        class AtCompleter(Completer):
            def __init__(self, root_dir: str):
                self.root_dir = root_dir

            def get_completions(self, document, complete_event):
                text = document.text_before_cursor
                if "@" not in text:
                    return
                idx = text.rindex("@")
                prefix = text[idx + 1:]

                from src.agents import list_agents
                for a in list_agents():
                    name = a["id"]
                    if name.startswith(prefix):
                        yield Completion(f"@{name}", start_position=-len(prefix) - 1, display=f"@{name}", display_meta=a.get("description", ""))

                root = Path(self.root_dir)
                for fpath in root.rglob("*"):
                    if fpath.is_file() and fpath.name.startswith(prefix):
                        rel = str(fpath.relative_to(root))
                        yield Completion(f"@{rel}", start_position=-len(prefix) - 1, display=f"@{rel}", display_meta="file")

        completer = AtCompleter(working_dir)
        psession = PromptSession(
            history=FileHistory(str(history_path)),
            completer=completer,
            complete_while_typing=True,
            key_bindings=kb,
        )
    except Exception:
        psession = PromptSession(key_bindings=kb)

    style = Style.from_dict({
        "prompt": "ansicyan bold",
    })

    console.print(Panel(
        "[bold cyan]EDSPiKE[/bold cyan] - AI Coding Assistant",
        subtitle="Type /help for commands, Tab to switch modes, Ctrl+C to exit",
        border_style="cyan",
    ))

    while True:
        mode = mode_mgr.get_current()
        color_code = {"build": "32", "plan": "33", "explore": "36", "general": "34"}.get(mode.id, "36")
        prompt_str = f"\033[{color_code}m[{mode.name}]\033[0m >>> "

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
    elif cmd in ("/init",):
        from src.cmd import run_command
        rc = run_command("init", [working_dir])
        if rc != 0:
            console.print("[red]/init failed[/red]")
    elif cmd in ("/connect",):
        from src.cmd import run_command
        rc = run_command("connect", [])
        if rc != 0:
            console.print("[red]/connect failed[/red]")
    elif cmd in ("/share",):
        from src.cmd import run_command
        rc = run_command("share", args)
        if rc != 0:
            console.print("[red]/share failed[/red]")
    elif cmd in ("/agent",) and args and args[0] == "create":
        from src.cmd import run_command
        rc = run_command("agent_create", args[1:])
        if rc != 0:
            console.print("[red]agent create failed[/red]")
    else:
        console.print(f"[red]Unknown command: {text}. Type /help for commands.[/red]")


def _process_prompt(text: str, console: Any, mode_mgr: Any, working_dir: str) -> None:
    try:
        from src.config import load_settings
        from src.providers import get_provider

        # Check for image paths (drag-drop support)
        extra_images = []
        for word in text.split():
            p = Path(word.strip("\"'"))
            if p.exists() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
                extra_images.append(str(p))

        settings = load_settings()
        provider = get_provider(settings.providers.default_provider or "openai")

        if not provider:
            console.print("[red]No provider configured. Run /connect[/red]")
            return

        model = settings.providers.default_model or "gpt-4"
        mode = mode_mgr.get_current()

        system_hints = {
            "plan": "You are in PLAN mode. Analyze and suggest changes but DO NOT modify any files.",
            "explore": "You are in EXPLORE mode. Search and read files only. Do not modify anything.",
        }
        hint = system_hints.get(mode.id, "")
        enhanced = text
        if hint:
            enhanced = f"[{mode.name} mode]\n{hint}\n\nUser: {text}"
        if extra_images:
            enhanced += "\n[Attached images: " + ", ".join(extra_images) + "]"

        with console.status("[cyan]Thinking...[/cyan]"):
            response = provider.generate(enhanced, model=model)

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
    table.add_row("Tab", "Switch between Build and Plan mode")
    table.add_row("/build", "Switch to Build mode (full access)")
    table.add_row("/plan", "Switch to Plan mode (read-only)")
    table.add_row("/mode [name]", "Show or switch agent mode")
    table.add_row("/undo", "Undo last file change")
    table.add_row("/diff", "Show recent file changes")
    table.add_row("/init", "Scan project and generate AGENTS.md")
    table.add_row("/connect", "Set up an AI provider")
    table.add_row("/share", "Create a shareable session link")
    table.add_row("/agent create", "Create a new agent")
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
            print("Commands: /help, /clear, /build, /plan, /mode, /undo, /diff, /init, /connect, /share, /exit, /quit")
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
