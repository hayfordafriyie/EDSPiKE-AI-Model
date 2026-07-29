from __future__ import annotations

from pathlib import Path
from typing import Any

from .registry import ToolSpec


DIAGNOSTICS_TOOL = ToolSpec(
    name="diagnostics",
    description="Get LSP diagnostics (errors, warnings) for a file. Returns all issues found by the language server.",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to check",
            },
            "language": {
                "type": "string",
                "description": "Programming language (e.g. python, javascript, typescript)",
                "default": "",
            },
        },
        "required": ["file_path"],
    },
)


def run_diagnostics(file_path: str, language: str = "") -> str:
    path = Path(file_path)
    if not path.exists():
        return f"Error: File not found: {file_path}"

    if not language:
        ext = path.suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescriptreact",
            ".jsx": "javascriptreact",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
        }
        language = lang_map.get(ext, "")

    if not language:
        return "Error: Could not determine language for diagnostics. Specify a language."

    server_map = {
        "python": ["pyright-langserver", "--stdio"],
        "javascript": ["typescript-language-server", "--stdio"],
        "typescript": ["typescript-language-server", "--stdio"],
        "typescriptreact": ["typescript-language-server", "--stdio"],
        "javascriptreact": ["typescript-language-server", "--stdio"],
        "go": ["gopls"],
        "rust": ["rust-analyzer"],
        "java": ["eclipse-jdtls"],
        "c": ["clangd"],
        "cpp": ["clangd"],
        "csharp": ["omnisharp"],
        "ruby": ["solargraph"],
        "php": ["intelephense"],
        "swift": ["sourcekit-lsp"],
    }

    server_cmd = server_map.get(language)
    if not server_cmd:
        return f"Error: No LSP server known for language: {language}"

    try:
        from src.lsp import LspClient

        root_uri = f"file://{path.parent}"
        client = LspClient(language, server_cmd, root_uri)
        client.start()
        file_uri = f"file://{path}"
        try:
            text = path.read_text()
        except Exception:
            text = ""
        client.open_document(file_uri, language, 1, text)
        items = client.get_diagnostics(file_uri)
        client.close_document(file_uri)
        client.shutdown()

        if not items:
            return f"No diagnostics for {file_path}"

        lines: list[str] = []
        for item in items:
            sev = {1: "ERROR", 2: "WARNING", 3: "INFO", 4: "HINT"}.get(item.get("severity", 0), "UNKNOWN")
            msg = item.get("message", "")
            r = item.get("range", {})
            start = r.get("start", {})
            line = start.get("line", 0) + 1
            col = start.get("character", 0)
            source = item.get("source", "")
            lines.append(f"{sev} L{line}:{col} [{source}] {msg}")

        return "\n".join(lines)

    except FileNotFoundError:
        return f"Error: LSP server not found for {language}. Install {server_cmd[0]}."
    except Exception as e:
        return f"Error running diagnostics: {e}"
