from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SharedSession:
    session_id: str
    owner_id: str
    shared_with: list[str] = field(default_factory=list)
    permission: str = "read"  # read, write, admin
    token: str = ""
    expires_at: float = 0.0
    created_at: float = 0.0


class SessionSharing:
    def __init__(self, data_dir: str):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._shares: dict[str, SharedSession] = {}
        self._load()

    def _path(self) -> Path:
        return self._data_dir / "shares.json"

    def _load(self) -> None:
        path = self._path()
        if path.exists():
            data = json.loads(path.read_text())
            for item in data:
                share = SharedSession(**item)
                self._shares[share.session_id] = share

    def _save(self) -> None:
        data = [s.__dict__ for s in self._shares.values()]
        self._path().write_text(json.dumps(data, indent=2))

    def share(self, session_id: str, owner_id: str, user_id: str, permission: str = "read", expires_in: float = 0) -> SharedSession:
        from src.ulid import ulid
        share = SharedSession(
            session_id=session_id,
            owner_id=owner_id,
            shared_with=[user_id],
            permission=permission,
            token=ulid(),
            expires_at=(time.time() + expires_in) if expires_in > 0 else 0,
            created_at=time.time(),
        )
        self._shares[session_id] = share
        self._save()
        return share

    def add_user(self, session_id: str, user_id: str) -> bool:
        share = self._shares.get(session_id)
        if not share:
            return False
        if user_id not in share.shared_with:
            share.shared_with.append(user_id)
            self._save()
        return True

    def remove_user(self, session_id: str, user_id: str) -> bool:
        share = self._shares.get(session_id)
        if not share or user_id not in share.shared_with:
            return False
        share.shared_with.remove(user_id)
        self._save()
        return True

    def check_access(self, session_id: str, user_id: str) -> str:
        share = self._shares.get(session_id)
        if not share:
            return "denied"
        if share.owner_id == user_id:
            return "admin"
        if share.expires_at and time.time() > share.expires_at:
            return "denied"
        if user_id in share.shared_with:
            return share.permission
        return "denied"

    def revoke(self, session_id: str, owner_id: str) -> bool:
        share = self._shares.get(session_id)
        if not share or share.owner_id != owner_id:
            return False
        del self._shares[session_id]
        self._save()
        return True

    def list_for_user(self, user_id: str) -> list[SharedSession]:
        return [s for s in self._shares.values()
                if s.owner_id == user_id or user_id in s.shared_with]

    def list_all(self) -> list[SharedSession]:
        return list(self._shares.values())
