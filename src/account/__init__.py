from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Account:
    id: str = ""
    name: str = ""
    email: str = ""
    role: str = "user"  # user, admin, bot
    provider: str = ""  # oauth provider
    disabled: bool = False
    created_at: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


class AccountManager:
    def __init__(self, data_dir: str):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._accounts: dict[str, Account] = {}
        self._load()

    def _path(self) -> Path:
        return self._data_dir / "accounts.json"

    def _load(self) -> None:
        path = self._path()
        if path.exists():
            data = json.loads(path.read_text())
            for item in data:
                acct = Account(**item)
                self._accounts[acct.id] = acct

    def _save(self) -> None:
        data = [acct.__dict__ for acct in self._accounts.values()]
        self._path().write_text(json.dumps(data, indent=2))

    def create(self, name: str, email: str = "", role: str = "user", provider: str = "", meta: dict | None = None) -> Account:
        from src.ulid import ulid
        acct = Account(
            id=ulid(),
            name=name, email=email, role=role,
            provider=provider, created_at=time.time(),
            meta=meta or {},
        )
        self._accounts[acct.id] = acct
        self._save()
        return acct

    def get(self, account_id: str) -> Account | None:
        return self._accounts.get(account_id)

    def get_by_email(self, email: str) -> Account | None:
        for acct in self._accounts.values():
            if acct.email == email:
                return acct
        return None

    def update(self, account_id: str, **kwargs: Any) -> Account | None:
        acct = self.get(account_id)
        if not acct:
            return None
        for key, value in kwargs.items():
            if hasattr(acct, key) and key not in ("id", "created_at"):
                setattr(acct, key, value)
        self._save()
        return acct

    def delete(self, account_id: str) -> bool:
        if account_id in self._accounts:
            del self._accounts[account_id]
            self._save()
            return True
        return False

    def list(self) -> list[Account]:
        return list(self._accounts.values())

    def count(self) -> int:
        return len(self._accounts)
