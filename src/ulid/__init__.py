from __future__ import annotations

import os
import time
from typing import ClassVar


EDSPIKE_EPOCH = 1700000000000  # custom epoch (ms)


class ULID:
    CROCKFORD: ClassVar[str] = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    BASE: ClassVar[int] = 32

    def __init__(self, value: str | None = None):
        if value:
            self._value = value.upper()
        else:
            self._value = self._generate()

    @classmethod
    def new(cls) -> ULID:
        return cls()

    @classmethod
    def from_str(cls, s: str) -> ULID:
        return cls(s)

    def _generate(self) -> str:
        now_ms = int(time.time() * 1000) - EDSPIKE_EPOCH
        timestamp = self._encode(now_ms, 10)
        random = self._encode(
            int.from_bytes(os.urandom(8), "big") >> 16, 16
        )
        return timestamp + random

    def _encode(self, value: int, length: int) -> str:
        chars: list[str] = []
        for _ in range(length):
            chars.append(self.CROCKFORD[value % self.BASE])
            value //= self.BASE
        return "".join(reversed(chars))

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"ULID('{self._value}')"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ULID) and self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)


def ulid() -> str:
    return str(ULID.new())
