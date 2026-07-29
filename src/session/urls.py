from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class SessionLink:
    session_id: str
    host: str = "edspike.ai"
    turn_index: int = -1  # -1 = latest
    agent_id: str = ""


SESSION_URL_PATTERN = re.compile(r"^https?://([^/]+)/share/([a-zA-Z0-9_-]+)(?:/(\d+))?(?:\?agent=([a-zA-Z0-9_-]+))?$")


def parse_session_url(url: str) -> SessionLink | None:
    match = SESSION_URL_PATTERN.match(url)
    if not match:
        return None
    return SessionLink(
        host=match.group(1),
        session_id=match.group(2),
        turn_index=int(match.group(3)) if match.group(3) else -1,
        agent_id=match.group(4) or "",
    )


def build_session_url(session_id: str, host: str = "edspike.ai", turn_index: int = -1, agent_id: str = "") -> str:
    url = f"https://{host}/share/{session_id}"
    if turn_index >= 0:
        url += f"/{turn_index}"
    if agent_id:
        url += f"?agent={agent_id}"
    return url


def is_valid_session_id(session_id: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_-]{8,64}$", session_id))
