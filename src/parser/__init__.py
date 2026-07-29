from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Any


MAX_PARSE_NODES = 5000
MAX_PARSE_DEPTH = 50


class ParseBudgetExceeded(Exception):
    pass


@dataclass
class ParseResult:
    ok: bool = True
    commands: list[str] = field(default_factory=list)
    commands_with_args: list[dict[str, Any]] = field(default_factory=list)
    has_sudo: bool = False
    has_redirect: bool = False
    has_pipe: bool = False
    has_var_assignment: bool = False
    error: str = ""


def parse_bash(text: str) -> ParseResult:
    result = ParseResult()
    if not text.strip():
        return result

    try:
        tokens = shlex.split(text)
    except ValueError as e:
        result.ok = False
        result.error = f"Lexer error: {e}"
        return result

    result.commands = _extract_commands(tokens, result)
    result.commands_with_args = _extract_commands_with_args(tokens)
    return result


def _extract_commands(tokens: list[str], result: ParseResult) -> list[str]:
    commands: list[str] = []
    for token in tokens:
        if "=" in token and not token.startswith("-") and not token.startswith("$"):
            result.has_var_assignment = True
    for token in tokens:
        if token in ("|", "|&"):
            result.has_pipe = True
        if token in (">", ">>", "<", "<<", "2>", "&>"):
            result.has_redirect = True
        if token == "sudo":
            result.has_sudo = True
    cmd = tokens[0] if tokens else ""
    if cmd:
        commands.append(cmd)
        for i, t in enumerate(tokens):
            if t in ("&&", "||", ";", "|"):
                if i + 1 < len(tokens):
                    commands.append(tokens[i + 1])
    return commands


def _extract_commands_with_args(tokens: list[str]) -> list[dict[str, Any]]:
    if not tokens:
        return []
    result: list[dict[str, Any]] = []
    current: dict[str, Any] = {"command": "", "args": []}
    for token in tokens:
        if token in ("&&", "||", ";", "|"):
            if current["command"]:
                result.append(current)
            current = {"command": "", "args": []}
        elif not current["command"]:
            current["command"] = token
        else:
            current["args"].append(token)
    if current["command"]:
        result.append(current)
    return result


def is_dangerous_command(text: str) -> tuple[bool, str]:
    result = parse_bash(text)
    if not result.ok:
        return False, ""

    dangerous_patterns = {
        "rm -rf /": "Recursive root delete",
        "rm -rf /*": "Recursive root delete",
        "mkfs": "Filesystem creation",
        "dd if=": "Raw disk write",
        "> /dev/sda": "Raw disk write",
        ":(){ :|:& };:": "Fork bomb",
        "chmod -R 000": "Mass permission removal",
        "wget": "Remote download (potential risk)",
        "curl": "Remote download (potential risk)",
    }

    for pattern, reason in dangerous_patterns.items():
        if pattern in text:
            return True, reason

    if result.has_sudo and ("rm" in result.commands or "dd" in result.commands):
        return True, "sudo with destructive command"

    return False, ""


def extract_git_commands(text: str) -> list[str]:
    result = parse_bash(text)
    return [cmd for cmd in result.commands if cmd in ("git", "gh", "gist")]
