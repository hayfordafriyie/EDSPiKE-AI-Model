from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any


SHARE_LINKS_FILE = Path.home() / ".edspike" / "share_links.json"


def _ensure_file() -> None:
    SHARE_LINKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not SHARE_LINKS_FILE.exists():
        SHARE_LINKS_FILE.write_text("[]")


def cmd_share(args: list[str]) -> int:
    _ensure_file()
    session_id = args[0] if args else f"sess_{int(time.time())}"

    link = f"https://edspike.ai/share/{session_id}"
    try:
        import pyperclip
        pyperclip.copy(link)
        clipboard_msg = " (copied to clipboard!)"
    except ImportError:
        clipboard_msg = ""

    links: list[dict[str, Any]] = json.loads(SHARE_LINKS_FILE.read_text())
    links.append({
        "session_id": session_id,
        "link": link,
        "created_at": time.time(),
    })
    SHARE_LINKS_FILE.write_text(json.dumps(links, indent=2))

    print(f"\nShared session: {link}{clipboard_msg}")
    return 0


def cmd_share_list(args: list[str]) -> int:
    _ensure_file()
    links: list[dict[str, Any]] = json.loads(SHARE_LINKS_FILE.read_text())
    if not links:
        print("No shared sessions.")
        return 0
    print("\nShared sessions:")
    for link in reversed(links[-10:]):
        print(f"  {link['link']}")
    return 0
