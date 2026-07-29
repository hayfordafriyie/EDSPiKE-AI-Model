from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


class Ok(Generic[T]):
    def __init__(self, value: T):
        self.ok = True
        self.value = value

    def unwrap(self) -> T:
        return self.value

    def unwrap_or(self, default: T) -> T:
        return self.value

    def map(self, fn: Callable[[T], Any]) -> Ok[Any]:
        return Ok(fn(self.value))

    def __repr__(self) -> str:
        return f"Ok({self.value!r})"


class Err(Generic[E]):
    def __init__(self, error: E):
        self.ok = False
        self.error = error

    def unwrap(self) -> None:
        raise ValueError(f"Called unwrap on Err: {self.error}")

    def unwrap_or(self, default: T) -> T:
        return default

    def map(self, fn: Callable[[T], Any]) -> Err[E]:
        return self

    def __repr__(self) -> str:
        return f"Err({self.error!r})"


Result = Ok[T] | Err[E]


def Ok_of(value: T) -> Ok[T]:
    return Ok(value)


def Err_of(error: E) -> Err[E]:
    return Err(error)


def result_from(fn: Callable[..., T], *args: Any, **kwargs: Any) -> Result[T, str]:
    try:
        return Ok(fn(*args, **kwargs))
    except Exception as e:
        return Err(str(e))
